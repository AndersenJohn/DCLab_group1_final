import gym
import numpy as np
from gym import spaces

from game_state import GameState
from state_encoder_p2 import StateEncoder

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

    def __init__(self):
        super().__init__()

        self.encoder = StateEncoder(max_bullets=8)

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

        return self.encoder.encode(self.gs), {}

    # ---------------------------------------------------------
    # step
    # ---------------------------------------------------------
    def step(self, action):
        gs = self.gs

        reward = 0
        done = False
        info = {}

        # ---------- P2 必須在 item phase / shoot phase 決策 ----------
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
        gs.turn = "p1"     # 每回合 P1 先行？你可改規則

        size = len(gs.real_bullets)
        gs.p1.bullet_knowledge = [None] * size
        gs.p2.bullet_knowledge = [None] * size

        self._give_items(gs.p1)
        self._give_items(gs.p2)

    # ---------------------------------------------------------
    # 給道具
    # ---------------------------------------------------------
    def _give_items(self, player, amount=2):
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
                return -0.1    # 用不了，輕微懲罰

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

        if action == 0:   # shoot enemy
            reward += self._shoot(gs, p, o)
        elif action == 1: # shoot self
            reward += self._shoot(gs, p, p)
        else:
            reward -= 0.2   # 射擊階段做奇怪行為懲罰

        return reward

    # ---------------------------------------------------------
    # 道具邏輯（簡版）
    # ---------------------------------------------------------
    def _use_item(self, player, opponent, gs, item):
        reward = 0

        if item == "magnifier":
            if gs.current_index < len(gs.real_bullets):
                k = gs.real_bullets[gs.current_index]
                player.bullet_knowledge[gs.current_index] = k
                reward += 0.05

        elif item == "cigarette":
            player.hp += 1
            reward += 0.1

        elif item == "beer":
            if gs.current_index < len(gs.real_bullets):
                removed = gs.real_bullets.pop(gs.current_index)

                if removed == "live":
                    gs.live_left -= 1
                else:
                    gs.blank_left -= 1

                player.bullet_knowledge[gs.current_index] = removed
                opponent.bullet_knowledge[gs.current_index] = removed

                gs.current_index += 1
                reward += 0.1

        elif item == "saw":
            gs.saw_active = True

        elif item == "handcuff":
            opponent.handcuffed = True
            reward += 0.05

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
    def _shoot(self, gs, shooter, victim):
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

            if victim is shooter:
                reward -= dmg * 0.2
            else:
                reward += dmg * 0.2

        else:  # blank
            gs.blank_left -= 1
            reward -= 0.02

        return reward

    # ---------------------------------------------------------
    # 遊戲結束獎勵
    # ---------------------------------------------------------
    def _calc_terminal_reward(self):
        if self.gs.p2.hp > 0 and self.gs.p1.hp <= 0:
            return +1
        else:
            return -1

    # ---------------------------------------------------------
    # render（debug）
    # ---------------------------------------------------------
    def render(self):
        print(f"P1 HP={self.gs.p1.hp}, P2 HP={self.gs.p2.hp}, phase={self.gs.phase}")
        print(f"Bullets: {self.gs.real_bullets}, idx={self.gs.current_index}")
