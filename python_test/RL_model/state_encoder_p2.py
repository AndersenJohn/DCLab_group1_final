import numpy as np
from game_state import GameState, PlayerState

class StateEncoder:
    def __init__(self, max_bullets=8):
        self.max_bullets = max_bullets

    def encode(self, gs: GameState) -> np.ndarray:
        vec = []

        # --------------------------------------------------------
        # 1. 全域資訊（雙方都知道）
        # --------------------------------------------------------
        vec.append(gs.live_left) 
        vec.append(gs.blank_left)
        vec.append(gs.current_index)
        vec.append(1 if gs.saw_active else 0)

        vec += self._encode_phase(gs.phase)

        # --------------------------------------------------------
        # 2. p2的資訊
        # --------------------------------------------------------
        vec += self._encode_self(gs.p2)

        # --------------------------------------------------------
        # 3. p1的資訊
        # --------------------------------------------------------
        vec += self._encode_self(gs.p1)

        # --------------------------------------------------------
        # 4. p2 的 bullet knowledge（AI 的視角）
        # --------------------------------------------------------
        vec += self._encode_bullet_knowledge(gs.p2.bullet_knowledge)

        return np.array(vec, dtype=np.float32)

    # ===========================
    # encode 道具
    # ===========================
    def _encode_self(self, p: PlayerState):
        items = p.items
        return [
            p.hp,
            1 if p.handcuffed else 0,

            items.magnifier,
            items.cigarette,
            items.beer,
            items.saw,
            items.handcuff,
            items.phone,
        ]
    # ===========================
    # encode bullet list + mask
    # ===========================
    def _encode_bullet_knowledge(self, knowledge):
        encode_map = {
            None: 1,
            "live": 2,
            "blank": 3,
        }

        values = []
        for k in knowledge:
            values.append(encode_map.get(k, 1))

        while len(values) < self.max_bullets:
            values.append(0)

        return values[:self.max_bullets] 

    # ===========================
    # encode game phase
    # ===========================
    def _encode_phase(self, phase: str):
        mapping = ["item", "shoot"]
        return [
            1.0 if phase == p else 0.0
            for p in mapping
        ]

