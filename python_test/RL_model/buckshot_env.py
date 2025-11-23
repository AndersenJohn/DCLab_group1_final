import gymnasium as gym
import numpy as np
from gymnasium import spaces

from game_state import GameState
from state_encoder_p2 import StateEncoder
from state_encoder_p1 import StateEncoder as StateEncoderP1

import random

VALID_COMBOS = [
    (1,3),(2,2),(3,1),
    (2,4),(3,3),(4,2),
    (3,5),(4,4),(5,3),
]

ITEM_LIST = ["magnifier", "cigarette", "beer", "saw", "handcuff", "phone" , "reverse"]
INVALID_ACTION_PENALTY = -8.0


class BuckshotEnv(gym.Env):
    """
    RL 專用 Buckshot Roulette 環境。
    P2 = agent
    P1 = rule-based 對手
    """

    metadata = {"render.modes": ["human"]}

    def __init__(self, opponent_model=None):
        super().__init__()

        self.encoder = StateEncoder(max_bullets=8)
        self.encoder_p1 = StateEncoderP1(max_bullets=8)
        self.opponent_model = opponent_model  # P1's model for self-play

        # 動作空間
        # 0: shoot enemy, 1: shoot self, 2..8: use items (7 items), 9: ready
        self.action_space = spaces.Discrete(10)

        # 狀態空間（定長向量）
        dummy = GameState()
        obs = self.encoder.encode(dummy)
        self.observation_space = spaces.Box(
            low=-999, high=999, shape=obs.shape, dtype=np.float32
        )

        self.gs = None

    # ---------------------------------------------------------
    # reset
    # ---------------------------------------------------------
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        self.gs = GameState()
        self._load_new_round()

        # If P1 goes first, execute P1's turn before returning to P2
        while self.gs.turn == "p1" and self.gs.phase != "game_end":
            self._opponent_turn()

            # Check if bullets ran out after P1's turn
            if self.gs.current_index >= len(self.gs.real_bullets):
                self._load_new_round()
                # Might be P1's turn again
                if self.gs.turn != "p2":
                    continue
                else:
                    break

            # Break if it's now P2's turn
            if self.gs.turn == "p2":
                break

        return self.encoder.encode(self.gs), {}

    # ---------------------------------------------------------
    # step
    # ---------------------------------------------------------
    def step(self, action):
        gs = self.gs

        reward = 0
        done = False
        info = {}

        # If P2 is handcuffed, skip P2's turn immediately and give control to P1
        # Clear the handcuff and pass the turn to P1
        if gs.turn == "p2" and gs.phase == "item" and gs.p2.handcuffed:
            gs.p2.handcuffed = False
            gs.turn = "p1"
            gs.phase = "item"
            # After skipping, execute P1's turn(s) before returning
            while gs.turn == "p1" and gs.phase != "game_end":
                self._opponent_turn()
                if gs.phase == "game_end":
                    done = True
                    reward += self._calc_terminal_reward()
                    return self.encoder.encode(gs), reward, done, False, info
                if gs.current_index >= len(gs.real_bullets):
                    self._load_new_round()
                    if gs.turn != "p2":
                        continue
                    else:
                        break
                if gs.turn == "p1":
                    continue
                else:
                    break

        # ---------- P2 行動 (item phase / shoot phase) ----------
        if gs.phase == "item":
            reward += self._apply_item_action(action)

        elif gs.phase == "shoot":
            reward += self._apply_shoot_action(action)

        # ---------- 處理回合結束 ----------
        if gs.phase == "game_end":
            done = True
            reward += self._calc_terminal_reward()
            return self.encoder.encode(gs), reward, done, False, info

        # ---------- 如果子彈打完，自動 load 下一 round ----------
        if gs.current_index >= len(gs.real_bullets):
            self._load_new_round()

        # ---------- P1 對手回合 (如果有 opponent_model) ----------
        # Keep executing P1's turns until it's P2's turn again or game ends
        while gs.turn == "p1" and gs.phase != "game_end":
            self._opponent_turn()

            # Check if game ended after P1's action
            if gs.phase == "game_end":
                done = True
                reward += self._calc_terminal_reward()
                return self.encoder.encode(gs), reward, done, False, info

            # Check if bullets ran out
            if gs.current_index >= len(gs.real_bullets):
                self._load_new_round()
                # After reload, it might be P1's turn again
                if gs.turn != "p2":
                    continue
                else:
                    break

            # If still P1's turn (shot self with blank), continue
            if gs.turn == "p1":
                continue
            else:
                break

        return self.encoder.encode(gs), reward, done, False, info

    # ---------------------------------------------------------
    # 內部邏輯：load new round
    # ---------------------------------------------------------
    def _load_new_round(self):
        gs = self.gs

        live, blank = random.choice(VALID_COMBOS)
        gs.live_left = live
        gs.blank_left = blank

        gs.real_bullets = ["live"] * live + ["blank"] * blank
        random.shuffle(gs.real_bullets)

        gs.current_index = 0
        gs.phase = "item"
        # Randomize who goes first each round for fairness
        gs.turn = random.choice(["p1", "p2"])

        size = len(gs.real_bullets)
        gs.p1.bullet_knowledge = [None] * size
        gs.p2.bullet_knowledge = [None] * size

        self._give_items(gs.p1)
        self._give_items(gs.p2)

    # ---------------------------------------------------------
    # 給道具
    # ---------------------------------------------------------
    def _give_items(self, player, amount=3):
        total = sum(vars(player.items).values())
        if total >= 6:
            return

        give_count = min(amount, 6 - total)
        pool = ITEM_LIST[:]
        random.shuffle(pool)
        selected = pool[:give_count]

        for item in selected:
            setattr(player.items, item, getattr(player.items, item) + 1)

    # ---------------------------------------------------------
    # P2 行為：item phase
    # ---------------------------------------------------------
    def _apply_item_action(self, action):
        gs = self.gs
        p = gs.p2
        o = gs.p1

        reward = 0

        # Disallow shooting actions during item phase: heavy penalty
        if action in (0, 1):
            return INVALID_ACTION_PENALTY

        # 9 = ready → 進入 shoot phase
        if action == 9:
            gs.phase = "shoot"
            return 0

        # 2~7 = use item
        item_index = action - 2

        if 0 <= item_index < len(ITEM_LIST):
            item = ITEM_LIST[item_index]

            if getattr(p.items, item) <= 0:
                return -1    # 用不了，輕微懲罰

            reward += self._use_item(p, o, gs, item)

        return reward

    # ---------------------------------------------------------
    # P2 行為：射擊
    # ---------------------------------------------------------
    def _apply_shoot_action(self, action):
        gs = self.gs
        p = gs.p2
        o = gs.p1

        reward = 0

        # Check if player knows the next bullet
        next_bullet_known = None
        if gs.current_index < len(p.bullet_knowledge):
            next_bullet_known = p.bullet_knowledge[gs.current_index]

        if action == 0:   # shoot enemy
            # Combo bonus: Using saw when you KNOW it's live
            if gs.saw_active and next_bullet_known == "live":
                reward += 2.0  # Smart combo!

            # Penalty: Shooting enemy when you KNOW it's blank
            if next_bullet_known == "blank":
                reward -= 2.0  # Terrible decision

            # Bonus: Shooting when you know it's live (without saw)
            elif next_bullet_known == "live":
                reward += 1.0  # Good decision

            reward += self._shoot(gs, p, o, target="enemy")

        elif action == 1: # shoot self
            # Bonus: Shooting self when you KNOW it's blank (extra turn)
            if next_bullet_known == "blank":
                reward += 2.0  # Excellent decision!

            # Penalty: Shooting self when you KNOW it's live
            elif next_bullet_known == "live":
                reward -= 3.0  # Why would you do this?!

            reward += self._shoot(gs, p, p, target="self")

        elif 2 <= action <= 9:
            # Trying to use items or ready during shoot phase - heavy invalid penalty
            reward += INVALID_ACTION_PENALTY

        else:
            # Any other invalid action
            reward += INVALID_ACTION_PENALTY

        return reward

    # ---------------------------------------------------------
    # 道具邏輯
    # ---------------------------------------------------------
    def _use_item(self, player, opponent, gs, item):
        reward = 0

        if item == "magnifier":
            if gs.current_index < len(gs.real_bullets):
                if player.bullet_knowledge[gs.current_index] is not None:
                    reward -= 1.0
 
                if gs.live_left == 0 or gs.blank_left == 0:
                    k = gs.real_bullets[gs.current_index]
                    player.bullet_knowledge[gs.current_index] = k
                    reward -= 1.0
                else:
                    k = gs.real_bullets[gs.current_index]
                    player.bullet_knowledge[gs.current_index] = k
                    reward += 1.0

        elif item == "cigarette":
            if player.hp >= 4:
                player.hp = 4
                reward -= 1.0  
            else:
                player.hp += 1
                reward += 1.0

        elif item == "beer":
            if gs.current_index < len(gs.real_bullets):
                if player.bullet_knowledge[gs.current_index] == "live":
                    reward -= 0.5
                elif player.bullet_knowledge[gs.current_index] == "blank":
                    reward -= 0.5
                else:
                    reward += 0.15
                
                removed = gs.real_bullets.pop(gs.current_index)
                player.bullet_knowledge[gs.current_index] = removed
                opponent.bullet_knowledge[gs.current_index] = removed
                if removed == "live":
                    gs.live_left -= 1
                else:
                    gs.blank_left -= 1
                gs.current_index += 1
                
        elif item == "saw":
            gs.saw_active = True
            if player.bullet_knowledge[gs.current_index] == "live":
                reward += 1.0  
            elif player.bullet_knowledge[gs.current_index] == "blank":
                reward -= 1.0
            else:
                reward += 0.15 
                
        elif item == "handcuff":
            opponent.handcuffed = True
            if gs.blank_left + gs.live_left <2:
                reward -= 1.0  
            reward += 0.5  

        elif item == "phone":
            total = len(gs.real_bullets)

            if total <= 3 and total > 0:
                last_bullet = gs.real_bullets[-1]
                player.bullet_knowledge[-1] = last_bullet
                reward += 0.12
            elif total > 3:
                candidates = [total - 3, total - 2, total - 1]
                chosen_idx = random.choice(candidates)
                chosen_bullet = gs.real_bullets[chosen_idx]
                player.bullet_knowledge[chosen_idx] = chosen_bullet
                reward += 0.12
            else:
                reward -= 0.5

        elif item == "reverse":
            gs.reverse_active = True
            
            if player.bullet_knowledge[gs.current_index] == "live":
                reward -= 1.0
            elif player.bullet_knowledge[gs.current_index] == "blank":
                reward -= 1.0
            else:
                 reward += 0.15
   
        setattr(player.items, item, getattr(player.items, item) - 1)

        return reward

    # ---------------------------------------------------------
    # 射擊邏輯
    # ---------------------------------------------------------
    def _shoot(self, gs, shooter, victim, target="enemy"):
        reward = 0
        # original bullet in the magazine
        orig_bullet = gs.real_bullets[gs.current_index]
        gs.current_index += 1

        # effect bullet may be flipped by reverse
        effect_bullet = "live" if (gs.reverse_active and orig_bullet == "blank") else (
            "blank" if (gs.reverse_active and orig_bullet == "live") else orig_bullet
        )

        dmg = 2 if gs.saw_active else 1
        gs.saw_active = False

        # follow main.py logic: decrement counters according to original bullet when reverse is active
        if effect_bullet == "blank":
            if gs.reverse_active:
                # flipped effect but consume original (live) count
                if victim == shooter:
                    gs.live_left -= 1
                    gs.turn = "p1" if gs.turn == "p1" else "p2"
                else:
                    gs.live_left -= 1
                    gs.turn = "p2" if gs.turn == "p1" else "p1"
            else:
                if victim == shooter:
                    gs.blank_left -= 1
                    gs.turn = "p1" if gs.turn == "p1" else "p2"
                else:
                    gs.blank_left -= 1
                    gs.turn = "p2" if gs.turn == "p1" else "p1"

        else:  # effect_bullet == live
            if gs.reverse_active:
                # flipped effect but consume original (blank) count
                if victim == shooter:
                    gs.blank_left -= 1
                    victim.hp -= dmg
                    gs.turn = "p2" if gs.turn == "p1" else "p1"
                else:
                    gs.blank_left -= 1
                    victim.hp -= dmg
                    gs.turn = "p2" if gs.turn == "p1" else "p1"
            else:
                if victim == shooter:
                    gs.live_left -= 1
                    victim.hp -= dmg
                    gs.turn = "p2" if gs.turn == "p1" else "p1"
                else:
                    gs.live_left -= 1
                    victim.hp -= dmg
                    gs.turn = "p2" if gs.turn == "p1" else "p1"

        # record knowledge using the effect bullet (what players observe)
        shooter.bullet_knowledge[gs.current_index - 1] = effect_bullet
        opponent = gs.p1 if shooter is gs.p2 else gs.p2
        opponent.bullet_knowledge[gs.current_index - 1] = effect_bullet

        if victim.hp <= 0:
            gs.phase = "game_end"

        return reward

    # ---------------------------------------------------------
    # 遊戲結束獎勵
    # ---------------------------------------------------------
    def _calc_terminal_reward(self):
        if self.gs.p2.hp > 0 and self.gs.p1.hp <= 0:
            return +10  # Victory!
        else:
            return -10  # Defeat

    # ---------------------------------------------------------
    # P1 對手行為（使用 opponent_model）
    # ---------------------------------------------------------
    def _opponent_turn(self):
        """Execute P1's turn using opponent model or random policy"""
        gs = self.gs

        # Handle handcuff (skip turn)
        if gs.p1.handcuffed:
            # Clear handcuff and pass the turn to P2
            gs.p1.handcuffed = False
            gs.turn = "p2"
            gs.phase = "item"
            return

        # action name labels removed (debug prints removed)

        # P1's item phase - use items or ready
        max_item_actions = 6  # Prevent infinite item usage
        item_actions_taken = 0

        while gs.phase == "item" and gs.turn == "p1" and item_actions_taken < max_item_actions:

            # Get action from model or random
            if self.opponent_model:
                obs_p1 = self.encoder_p1.encode(gs)
                action, _ = self.opponent_model.predict(obs_p1, deterministic=False)
            else:
                # Random action when no model - bias towards ready to avoid infinite loop
                if random.random() < 0.3:  # 30% chance to use item
                    action = random.randint(2, 8)
                else:
                    action = 9  # ready

            # action logging removed

            if action == 9:  # ready
                gs.phase = "shoot"
                break  # Exit item phase
            elif 2 <= action <= 8:
                # Use item
                item_index = action - 2
                if 0 <= item_index < len(ITEM_LIST):
                    item = ITEM_LIST[item_index]
                    if getattr(gs.p1.items, item) > 0:
                        self._use_item(gs.p1, gs.p2, gs, item)
                        item_actions_taken += 1
                    else:
                        # Invalid item, try ready instead
                        gs.phase = "shoot"
                        break
                else:
                    gs.phase = "shoot"
                    break
            else:
                # Invalid action in item phase, go to shoot
                gs.phase = "shoot"
                break

        # P1's shoot phase
        if gs.phase == "shoot" and gs.turn == "p1":
            # P1 shoot phase (debug output removed)
            # Check if bullets ran out before shooting
            if gs.current_index >= len(gs.real_bullets):
                self._load_new_round()
                # After reload, might not be P1's turn anymore
                return

            # Get action from model or random
            if self.opponent_model:
                obs_p1 = self.encoder_p1.encode(gs)
                action, _ = self.opponent_model.predict(obs_p1, deterministic=False)
            else:
                # Random shoot action (0 or 1)
                action = random.randint(0, 1)


            if action == 0:  # shoot enemy (P2)
                self._shoot(gs, gs.p1, gs.p2, target="enemy")
            elif action == 1:  # shoot self
                self._shoot(gs, gs.p1, gs.p1, target="self")
            else:
                # Invalid action, default to shoot enemy
                self._shoot(gs, gs.p1, gs.p2, target="enemy")

    # ---------------------------------------------------------
    # Action Masking（用於 MaskablePPO）
    # ---------------------------------------------------------
    def action_masks(self):
        """
        Returns binary mask for valid actions.
        1 = valid action, 0 = invalid action
        Required by MaskablePPO from sb3-contrib
        """
        gs = self.gs
        mask = np.zeros(10, dtype=np.int8)

        if gs.phase == "item":
            # Item phase: can use items (2-7) or ready (8)
            p = gs.p2

            # Action 2-8: Use items (only if you have them) -> maps to ITEM_LIST (7 items)
            mask[2] = 1 if p.items.magnifier > 0 else 0
            mask[3] = 1 if p.items.cigarette > 0 else 0
            mask[4] = 1 if p.items.beer > 0 else 0
            mask[5] = 1 if p.items.saw > 0 else 0
            mask[6] = 1 if p.items.handcuff > 0 else 0
            mask[7] = 1 if p.items.phone > 0 else 0
            mask[8] = 1 if p.items.reverse > 0 else 0

            # Action 9: Ready (always valid in item phase)
            mask[9] = 1

        elif gs.phase == "shoot":
            # Shoot phase: can only shoot (0 or 1)
            mask[0] = 1  # shoot enemy
            mask[1] = 1  # shoot self

        return mask
