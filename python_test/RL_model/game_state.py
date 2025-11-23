from dataclasses import dataclass, field
from typing import List, Dict, Optional


# ========================
# 道具狀態（只記數量）
# ========================
@dataclass
class ItemState:
    magnifier: int = 0         # 放大鏡 - 查看下一發
    cigarette: int = 0         # 香菸 - +1HP
    beer: int = 0              # 啤酒 - 彈出子彈＋跳過回合
    saw: int = 0               # 手鋸 - 2倍傷害
    handcuff: int = 0          # 手銬 - 對手下一回合不能行動
    phone: int = 0             # 一次性手機 - 查詢任意剩餘子彈 必須為序位靠後的子彈
    reverse: int = 0          # 逆轉器 - live <-> blank
    #adrenaline: int = 0        # 腎上腺素 - 偷一件對手物品並立刻使用
    #medicine: int = 0          # 藥品 - 50% 回復2HP 50% 扣1HP
# ========================
# 玩家資訊
# ========================
@dataclass
class PlayerState:
    name: str
    hp: int = 4
    items: ItemState = field(default_factory=ItemState)

    # 對彈匣的了解（None 表示不知道）
    bullet_knowledge: List[Optional[str]] = field(default_factory=list)
    
    # 手銬效果（下一回合不能動）
    handcuffed: bool = False

# ========================
# 整個遊戲狀態
# ========================
@dataclass
class GameState:
    p1: PlayerState = field(default_factory=lambda: PlayerState(name="Player1"))
    p2: PlayerState = field(default_factory=lambda: PlayerState(name="Player2"))
    
    match: int = 1
    
    turn: str = "p1"

    # 真實彈匣（例如 ["live","blank","live"]）
    real_bullets: List[str] = field(default_factory=list)
    current_index: int = 0
    
    #剩餘子彈數量
    live_left: int = 0
    blank_left: int = 0
    
    # 本次射擊狀態（非持續性）
    saw_active: bool = False
    
    reverse_active: bool = False
    
    # 階段
    phase: str = "load"
    """
    load       = 裝彈階段，發道具 (default)
    item  = 使用物品
    shoot = 射擊階段
    game_end   = 其中一人死亡，遊戲結束
    """
    
    # 工具方法
    def get_current_player(self) -> PlayerState:
        return self.p1 if self.turn == "p1" else self.p2

    def get_opponent(self) -> PlayerState:
        return self.p2 if self.turn == "p1" else self.p1
