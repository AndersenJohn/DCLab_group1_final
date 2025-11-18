import gymnasium as gym
import numpy as np
from gymnasium import spaces

from game_state import GameState
from state_encoder_p2 import StateEncoder
from state_encoder_p1 import StateEncoder as StateEncoderP1

import random

VALID_COMBOS = [
    (1,1),
    (1,2),(2,1),
    (1,3),(2,2),(3,1),
    (2,3),(3,2),
    (2,4),(3,3),(4,2),
    (3,4),(4,3),
    (3,5),(4,4),(5,3),
]

ITEM_LIST = ["magnifier", "cigarette", "beer", "saw", "handcuff", "phone"]

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
        self.action_space = spaces.Discrete(9)

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

        # 8 = ready → 進入 shoot phase
        if action == 8:
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
                reward += 0.35  # Smart combo!

            # Penalty: Shooting enemy when you KNOW it's blank
            if next_bullet_known == "blank":
                reward -= 0.4  # Terrible decision

            # Bonus: Shooting when you know it's live (without saw)
            elif next_bullet_known == "live":
                reward += 0.2  # Good decision

            reward += self._shoot(gs, p, o, target="enemy")

        elif action == 1: # shoot self
            # Bonus: Shooting self when you KNOW it's blank (extra turn)
            if next_bullet_known == "blank":
                reward += 0.3  # Excellent decision!

            # Penalty: Shooting self when you KNOW it's live
            elif next_bullet_known == "live":
                reward -= 0.5  # Why would you do this?!

            reward += self._shoot(gs, p, p, target="self")

        elif 2 <= action <= 7:
            # Trying to use items during shoot phase - invalid!
            reward -= 1.0

        elif action == 8:
            # Trying to "ready" during shoot phase - invalid!
            reward -= 1.0

        else:
            # Any other invalid action
            reward -= 1.0

        return reward

    # ---------------------------------------------------------
    # 道具邏輯（簡版）
    # ---------------------------------------------------------
    def _use_item(self, player, opponent, gs, item):
        reward = 0

        if item == "magnifier":
            if gs.current_index < len(gs.real_bullets):
                # Penalize using magnifier when all remaining bullets are known
                if gs.live_left == 0 or gs.blank_left == 0:
                    # Wasteful - you already know what all bullets are!
                    k = gs.real_bullets[gs.current_index]
                    player.bullet_knowledge[gs.current_index] = k
                    reward -= 0.3
                else:
                    k = gs.real_bullets[gs.current_index]
                    player.bullet_knowledge[gs.current_index] = k
                    reward += 0.3

        elif item == "cigarette":
            if player.hp >= 4:
                player.hp = 4
                reward -= 0.5
            else:
                player.hp += 1
                reward += 0.3

        elif item == "beer":
            if gs.current_index < len(gs.real_bullets):
                removed = gs.real_bullets.pop(gs.current_index)

                if removed == "live":
                    gs.live_left -= 1
                    reward += 0.15  # Good! Removed danger
                else:
                    gs.blank_left -= 1
                    reward += 0.08  # OK, got info

                player.bullet_knowledge[gs.current_index] = removed
                opponent.bullet_knowledge[gs.current_index] = removed

                gs.current_index += 1

        elif item == "saw":
            gs.saw_active = True
            reward += 0.15  # Powerful item

        elif item == "handcuff":
            opponent.handcuffed = True
            reward += 0.3  # Strong control

        elif item == "phone":
            total = len(gs.real_bullets)
            if total > 0:
                idx = random.randint(0, total - 1)
                b = gs.real_bullets[idx]
                player.bullet_knowledge[idx] = b
                reward += 0.05

        # 消耗道具
        setattr(player.items, item, getattr(player.items, item) - 1)

        return reward

    # ---------------------------------------------------------
    # 射擊邏輯
    # ---------------------------------------------------------
    def _shoot(self, gs, shooter, victim, target="enemy"):
        reward = 0

        bullet = gs.real_bullets[gs.current_index]
        gs.current_index += 1

        dmg = 2 if gs.saw_active else 1
        gs.saw_active = False

        if bullet == "live":
            victim.hp -= dmg
            gs.live_left -= 1

            if victim.hp <= 0:
                gs.phase = "game_end"
                return reward

            if victim is shooter:
                # Shot self with live - bad!
                reward -= dmg * 1.0
            else:
                # Shot enemy with live - good!
                base_reward = dmg * 0.4

                # Bonus for finishing off low HP opponent
                if victim.hp <= 1 and victim.hp > -dmg:
                    base_reward += 0.3  # Close to winning

                reward += base_reward

            # Turn switches after shooting live (regardless of target)
            gs.turn = "p2" if gs.turn == "p1" else "p1"
            gs.phase = "item"

        else:  # blank
            gs.blank_left -= 1

            if target == "self":
                # Shot self with blank - GOOD! (Extra turn)
                reward += 0.15
                # Keep same turn (extra turn!)
            else:
                # Shot enemy with blank - wasted turn
                reward -= 0.1
                # Turn switches
                gs.turn = "p2" if gs.turn == "p1" else "p1"
                gs.phase = "item"

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
            gs.p1.handcuffed = False
            gs.turn = "p2"
            gs.phase = "item"
            return

        # P1's item phase - use items or ready
        max_item_actions = 10  # Prevent infinite item usage
        item_actions_taken = 0

        while gs.phase == "item" and gs.turn == "p1" and item_actions_taken < max_item_actions:
            # Get action from model or random
            if self.opponent_model:
                obs_p1 = self.encoder_p1.encode(gs)
                action, _ = self.opponent_model.predict(obs_p1, deterministic=False)
            else:
                # Random action when no model - bias towards ready to avoid infinite loop
                if random.random() < 0.3:  # 30% chance to use item
                    action = random.randint(2, 7)
                else:
                    action = 8  # ready

            if action == 8:  # ready
                gs.phase = "shoot"
                break  # Exit item phase
            elif 2 <= action <= 7:
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
        mask = np.zeros(9, dtype=np.int8)

        if gs.phase == "item":
            # Item phase: can use items (2-7) or ready (8)
            p = gs.p2

            # Action 2-7: Use items (only if you have them)
            mask[2] = 1 if p.items.magnifier > 0 else 0
            mask[3] = 1 if p.items.cigarette > 0 else 0
            mask[4] = 1 if p.items.beer > 0 else 0
            mask[5] = 1 if p.items.saw > 0 else 0
            mask[6] = 1 if p.items.handcuff > 0 else 0
            mask[7] = 1 if p.items.phone > 0 else 0

            # Action 8: Ready (always valid in item phase)
            mask[8] = 1

        elif gs.phase == "shoot":
            # Shoot phase: can only shoot (0 or 1)
            mask[0] = 1  # shoot enemy
            mask[1] = 1  # shoot self

        return mask

    # ---------------------------------------------------------
    # render（debug）
    # ---------------------------------------------------------
    def render(self):
        print(f"P1 HP={self.gs.p1.hp}, P2 HP={self.gs.p2.hp}, phase={self.gs.phase}")
        print(f"Bullets: {self.gs.real_bullets}, idx={self.gs.current_index}")
