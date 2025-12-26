import argparse
import shlex
import random
from game_state import GameState
from state_encoder_p2 import StateEncoder

# ================================
# 彈匣生成規則
# ================================
VALID_COMBOS = [
    (1,1),
    (1,2),(2,1),
    (1,3),(2,2),(3,1),
    (2,3),(3,2),
    (2,4),(3,3),(4,2),
    (3,4),(4,3),
    (3,5),(4,4),(5,3),
]

def generate_bullet_counts():
    return random.choice(VALID_COMBOS)

# ================================
# 顯示（debug）
# ================================
def show(gs: GameState):
    print("\n===== GameState =====")
    print(f"Match: {gs.match}")
    print(f"Turn: {gs.turn}")
    print(f"Phase: {gs.phase}")
    print(f"Real bullets: {gs.real_bullets}")
    print(f"Current index: {gs.current_index}")
    print(f"Live left: {gs.live_left}")
    print(f"Blank left: {gs.blank_left}")
    print(f"Saw active: {gs.saw_active}")

    print("\n-- Player 1 --")
    print(f"HP: {gs.p1.hp}")
    print(f"Items: {gs.p1.items}")
    print(f"Knowledge: {gs.p1.bullet_knowledge}")
    print(f"Handcuffed: {gs.p1.handcuffed}")

    print("\n-- Player 2 --")
    print(f"HP: {gs.p2.hp}")
    print(f"Items: {gs.p2.items}")
    print(f"Knowledge: {gs.p2.bullet_knowledge}")
    print(f"Handcuffed: {gs.p2.handcuffed}")

    print("====================\n")


# ================================
# argparse 指令
# ================================
def parse_command(command: str):
    parser = argparse.ArgumentParser(prog="", add_help=False)
    subparsers = parser.add_subparsers(dest="action")

    subparsers.add_parser("show")
    
    subparsers.add_parser("state")

    use_parser = subparsers.add_parser("use")
    use_parser.add_argument("item")
    
    subparsers.add_parser("ready")
    
    shoot_parser = subparsers.add_parser("shoot")
    shoot_parser.add_argument("target")

    subparsers.add_parser("help")

    try:
        args = parser.parse_args(shlex.split(command))
        return args
    except SystemExit:
        return None

# ================================
# 道具生成邏輯
# ================================
ITEM_POOL = [
    "magnifier", "cigarette", "beer", "saw",
    "handcuff", "phone"]

def give_random_items(player, amount=2):
    """每輪補 amount(=2) 個道具，但玩家最大只能有 6 個。"""

    # 計算現有道具總數
    total = sum(vars(player.items).values())

    if total >= 6:
        print(f"{player.name} 道具已達上限（6 個）")
        return

    # 本次最多補到不超過 6
    give_count = min(amount, 6 - total)

    # 洗牌道具池，確保分布更亂、更均勻
    pool = ITEM_POOL[:]   # copy 避免動到原本的
    random.shuffle(pool)

    # 取前 give_count 個道具
    selected = pool[:give_count]

    for item in selected:
        setattr(player.items, item, getattr(player.items, item) + 1)
        print(f"{player.name} 獲得道具：{item}")

# ================================
# 道具使用邏輯
# ================================
def handle_use(gs: GameState, item: str):
    player = gs.get_current_player()
    opponent = gs.get_opponent()

    if getattr(player.items, item, 0) <= 0:
        print(f"你沒有 {item}")
        return

    if item == "magnifier":
        if gs.current_index < len(gs.real_bullets):
            print(f"放大鏡：下一發是 {gs.real_bullets[gs.current_index]}")
            player.bullet_knowledge[gs.current_index] = gs.real_bullets[gs.current_index]

    elif item == "cigarette":
        player.hp += 1
        print("你抽了香菸，+1HP")

    elif item == "beer":
        removed = gs.real_bullets.pop(gs.current_index)

        # reveal 給雙方
        player.bullet_knowledge[gs.current_index] = removed
        opponent.bullet_knowledge[gs.current_index] = removed

        # 更新 live / blank 數量
        if removed == "live":
            gs.live_left -= 1
        else:
            gs.blank_left -= 1

        print(f"啤酒：彈出 {removed}，跳過本回合")
        gs.current_index += 1
    
    elif item == "saw":
        gs.saw_active = True
        print("手鋸：雙倍傷害啟動")

    elif item == "handcuff":
        gs.get_opponent().handcuffed = True
        print("手銬：對手下一回合無法行動")

    elif item == "phone":
        total = len(gs.real_bullets)

        # 如果總子彈 <= 3 → 直接顯示最後一發
        if total <= 3:
            last_bullet = gs.real_bullets[-1]
            player.bullet_knowledge[-1] = last_bullet
            print(f"一次性手機：彈匣最後一發是 {last_bullet}")
            return

        # 倒數三發的 index： total-3, total-2, total-1
        candidates = [total - 3, total - 2, total - 1]
        chosen_idx = random.choice(candidates)
        chosen_bullet = gs.real_bullets[chosen_idx]
        player.bullet_knowledge[chosen_idx] = chosen_bullet
        print(f"一次性手機：倒數第 {total - chosen_idx} 發是 {chosen_bullet}")
    
    # 消耗道具
    setattr(player.items, item, getattr(player.items, item) - 1)

# ================================
# 射擊邏輯
# ================================
def handle_shoot(gs: GameState, target: str):
    player = gs.get_current_player()
    opponent = gs.get_opponent()

    bullet = gs.real_bullets[gs.current_index]
    gs.current_index += 1

    victim = player if target == "self" else opponent

    damage = 2 if gs.saw_active else 1
    gs.saw_active = False

    if bullet == "blank":
        gs.blank_left -= 1
        if victim == player:
            print(f"砰！空包彈 → {victim.name} 無傷")
            gs.turn = "p1" if gs.turn == "p1" else "p2"
        else:
            print(f"砰！空包彈 → {victim.name} 無傷")
            gs.turn = "p2" if gs.turn == "p1" else "p1"       
    else:
        print(f"砰！實彈 → {victim.name} 受傷 {damage}")
        gs.live_left -= 1
        victim.hp -= damage
        gs.turn = "p2" if gs.turn == "p1" else "p1"
        
    player.bullet_knowledge[gs.current_index - 1] = bullet
    opponent.bullet_knowledge[gs.current_index - 1] = bullet    
    
    if victim.hp <= 0:
        gs.phase = "game_end"
        print(f"{victim.name} 死亡 → 遊戲結束")
        
# ================================
# RL State Encoder
# ================================
encoder = StateEncoder()
def show_state_encoding(gs, encoder):
    state_vec = encoder.encode(gs)
    print("\n===== Encoded State =====")
    print(state_vec)
    print(f"Vector length = {len(state_vec)}")
    print("=========================\n")

# ================================
# Main Loop (FSM)
# ================================
def main_loop(gs: GameState):
    while True:
        # ==========  Load Phase ==========
        if gs.phase == "load":
            print("\n=== 裝彈階段 ===")

            # 套用規則
            live, blank = generate_bullet_counts()
            gs.live_left, gs.blank_left = live, blank

            print(f"本輪子彈數：live={live}, blank={blank}")

            gs.real_bullets = ["live"] * live + ["blank"] * blank
            random.shuffle(gs.real_bullets)

            gs.current_index = 0

            # 初始化玩家知識
            size = len(gs.real_bullets)
            gs.p1.bullet_knowledge = [None] * size
            gs.p2.bullet_knowledge = [None] * size
            
            # 發放道具
            give_random_items(gs.p1)
            give_random_items(gs.p2)
            
            gs.phase = "item"
            continue
        
        # 手銬跳過回合
        player = gs.get_current_player()
        if player.handcuffed:
            print(f"{player.name} 被手銬 → 跳過回合")
            player.handcuffed = False
            gs.turn = "p2" if gs.turn == "p1" else "p1"
            continue
        # ========== Item Phase ==========
        if gs.phase == "item":
            print(f"\n=== 道具階段（{gs.turn}）===")
            print(f"\np1道具: {gs.p1.items}\np2道具: {gs.p2.items}")
            command = input(f"[{gs.turn}] >> ")
            args = parse_command(command)

            if args == "ready":
                gs.phase = "shoot"
                
            elif args.action == "show":
                show(gs)
            
            elif args.action == "state":
                show_state_encoding(gs, encoder)
            
            elif args.action == "use":
                handle_use(gs, args.item)
            
            elif args.action == "ready":
                gs.phase = "shoot"
        # ========== shoot Phase ==========    
        if gs.phase == "shoot":
            print(f"\n=== 射擊階段（{gs.turn}）===")
            command = input(f"[{gs.turn}] >> ")
            args = parse_command(command)

            if args.action == "show":
                show(gs)
                
            elif args.action == "state":
                show_state_encoding(gs, encoder)    

            elif args.action == "shoot":
                if args.target not in ("self", "enemy"):
                    print("shoot 只能 self 或 enemy")
                    continue
                handle_shoot(gs, args.target)
                if gs.phase != "game_end":
                    if gs.current_index >= len(gs.real_bullets):
                        gs.phase = "load"
                        print("\n=== 回合結束，準備下一輪 ===")
                    else:
                        gs.phase = "item"
        # ========== game_end Phase ==========
        if gs.phase == "game_end":
            print("\n=== 遊戲結束 ===")
            winner = gs.p1 if gs.p1.hp > 0 else gs.p2
            print(f"{winner.name} 獲勝！")
            break


if __name__ == "__main__":
    gs = GameState()
    main_loop(gs)
