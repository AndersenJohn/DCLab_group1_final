from game_state import GameState


def print_state(gs: GameState):
    print("\n===== GameState =====")
    print(f"Match: {gs.match}")
    print(f"Turn: {gs.turn}")
    print(f"Phase: {gs.phase}")
    print(f"Real bullets: {gs.real_bullets}")
    print(f"Current index: {gs.current_index}")
    print(f"Live left: {gs.live_left}")
    print(f"Blank left: {gs.blank_left}")
    print(f"Saw active: {gs.saw_active}")
    print(f"Inverter active: {gs.inverter_active}")

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


def test():
    gs = GameState()

    print("Buckshot Roulette GameState Controller")
    print("輸入 help 查看指令")

    while True:
        cmd = input(">> ").strip().lower()

        if cmd == "help":
            print("""
指令：
  show                 - 顯示 GameState
  hp p1 X              - 修改 p1 血量
  hp p2 X              - 修改 p2 血量
  additem p1 beer X    - 增加 p1 X 個指定道具
  turn p1/p2           - 設定回合
  knowledge p1/p2 idx val - 設定彈匣知識
  left live/blank X  - 設定剩餘子彈數量
  bullets a b c ...    - 設定彈匣（live/blank）
  clear                - 清空彈匣
  next                 - current_index += 1
  phase load/turn/...  - 設定 phase
  exit                 - 離開
""")

        elif cmd == "show":
            print_state(gs)

        elif cmd.startswith("hp"):
            _, who, val = cmd.split()
            val = int(val)
            if who == "p1":
                gs.p1.hp = val
            else:
                gs.p2.hp = val

        elif cmd.startswith("additem"):
            _, who, item, number = cmd.split()
            player = gs.p1 if who == "p1" else gs.p2
            if hasattr(player.items, item):
                setattr(player.items, item, getattr(player.items, item) + int(number))
                print(f"{who} 的 {item} 增加 {number}")
            else:
                print("沒有這個道具名稱")

        elif cmd.startswith("turn"):
            _, who = cmd.split()
            gs.turn = who

        elif cmd.startswith("knowledge"):
            _, who, idx, val = cmd.split()
            idx = int(idx)
            player = gs.p1 if who == "p1" else gs.p2
            # 若長度不夠，補到 idx
            while len(player.bullet_knowledge) <= idx:
                player.bullet_knowledge.append(None)
            # 寫入玩家看到的資訊
            player.bullet_knowledge[idx] = val
            print(f"{who} 的彈匣知識第 {idx} 發設為 {val}")

        elif cmd.startswith("left"):
            _, bullet_type, number = cmd.split()
            number = int(number)
            if bullet_type == "live":
                gs.live_left = number
            else:
                gs.blank_left = number
        
        elif cmd.startswith("bullets"):
            parts = cmd.split()[1:]
            gs.real_bullets = parts
            gs.current_index = 0
            print("彈匣已更新")
            
        elif cmd.startswith("clear"):
            parts = cmd
            gs.real_bullets = []
            gs.current_index = 0
            print("彈匣已清空")
            gs.p1.bullet_knowledge = []
            gs.p2.bullet_knowledge = []
        
        elif cmd == "next":
            gs.current_index += 1

        elif cmd == "exit":
            break
        
        elif cmd.startswith("phase"):
            _, ph = cmd.split()
            gs.phase = ph
            
        else:
            print("未知指令，輸入 help 查看")

if __name__ == "__main__":
    test()
