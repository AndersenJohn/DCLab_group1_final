"""
Play Buckshot Roulette against the trained AI.
Human = P1, AI = P2.

- 遊戲邏輯：完全使用 buckshot_env.BuckshotEnv 內部的 _use_item / _shoot / _load_new_round
- 操作介面：沿用 main.py 的指令介面 (show / state / use / ready / shoot)
"""

import argparse
import shlex

import random
import numpy as np
from sb3_contrib import MaskablePPO

from buckshot_env import BuckshotEnv, ITEM_LIST
from game_state import GameState
from state_encoder_p2 import StateEncoder as StateEncoderP2  # P2 視角 encoder (給 RL 用)

def _use_item(player, opponent, gs, item):
    reward = 0

    print(f"\n🧩 {player.name} 使用了 {item.upper()}")

    if item == "magnifier":
        if gs.current_index < len(gs.real_bullets):
            if player.bullet_knowledge[gs.current_index] is not None:
                print("🔍 你已經知道這顆子彈，不需要再查看。")
                reward -= 1.0
            else:
                if gs.live_left == 0 or gs.blank_left == 0:
                    k = gs.real_bullets[gs.current_index]
                    player.bullet_knowledge[gs.current_index] = k
                    print(f"🔍 查看結果：第 {gs.current_index+1} 顆子彈是 {k.upper()}（其實可推知）")
                    reward -= 1.0
                else:
                    k = gs.real_bullets[gs.current_index]
                    player.bullet_knowledge[gs.current_index] = k
                    print(f"🔍 查看結果：第 {gs.current_index+1} 顆子彈是 {k.upper()}！")
                    reward += 1.0

    elif item == "cigarette":
        if player.hp >= 4:
            player.hp = 4
            print("🚬 嘗試抽菸，但血量已滿。")
            reward -= 1.0  
        else:
            player.hp += 1
            print(f"🚬 抽菸恢復 1 HP，目前血量 = {player.hp}")
            reward += 1.0

    elif item == "beer":
        if gs.current_index < len(gs.real_bullets):
            removed = gs.real_bullets[gs.current_index]
            player.bullet_knowledge[gs.current_index] = removed
            opponent.bullet_knowledge[gs.current_index] = removed
            if removed == "live":
                gs.live_left -= 1
            else:
                gs.blank_left -= 1
            gs.current_index += 1
            print(f"🍺 喝啤酒移除一顆 {removed.upper()} 子彈。")
            reward += 0.15
        else:
            print("🍺 沒有子彈可移除，啤酒沒有效果。")
            reward -= 1.0
                        
    elif item == "saw":
        gs.saw_active = True
        print("🪚 鋸子啟用：本回合傷害 2 倍！")
        if gs.current_index < len(player.bullet_knowledge):
            if player.bullet_knowledge[gs.current_index] == "live":
                reward += 1.0
            elif player.bullet_knowledge[gs.current_index] == "blank":
                reward -= 1.0
            else:
                reward += 0.15

    elif item == "handcuff":
        opponent.handcuffed = True
        print(f"⛓️ {opponent.name} 被手銬限制，下回合將被跳過！")
        if gs.blank_left + gs.live_left < 2:
            reward += 0.3
        reward += 1.2  

    elif item == "phone":
        remaining_count = len(gs.real_bullets) - gs.current_index
        if remaining_count <= 0:
            print("📱 沒有剩餘子彈，手機無效。")
            reward -= 1.0
        elif remaining_count <= 3:
            last_idx = len(gs.real_bullets) - 1
            player.bullet_knowledge[last_idx] = gs.real_bullets[last_idx]
            print(f"📱 手機揭示最後一顆子彈：{gs.real_bullets[last_idx].upper()}")
            reward += 0.5
        else:
            last_idx = len(gs.real_bullets) - 1
            candidates = [last_idx - 2, last_idx - 1, last_idx]
            candidates = [idx for idx in candidates if idx >= gs.current_index]
            chosen_idx = random.choice(candidates)
            player.bullet_knowledge[chosen_idx] = gs.real_bullets[chosen_idx]
            print(f"📱 手機揭示第 {chosen_idx+1} 顆子彈：{gs.real_bullets[chosen_idx].upper()}")
            reward += 0.5

    elif item == "reverse":
        gs.reverse_active = True
        print("🔄 啟用 REVERSE！將會互換子彈效果。")
        if gs.current_index < len(player.bullet_knowledge):
            reward += 0.5
        else:
            reward += 0.15

    setattr(player.items, item, getattr(player.items, item) - 1)
    print(f"🎒 {player.name} 的 {item} 剩餘數量：{getattr(player.items, item)}\n")

    return reward
# ================================
# 顯示用工具：跟 main.py 類似
# ================================
def show(gs: GameState):
    """顯示目前狀態：血量、子彈、雙方道具"""
    print("\n" + "=" * 70)
    print("Round Info")
    print("-" * 70)
    print(f"Turn: {gs.turn} ({'Your turn' if gs.turn == 'p1' else 'AI turn'})")
    print(f"Phase: {gs.phase}")
    print(f"Bullets: live={gs.live_left} blank={gs.blank_left} "
          f"(剩餘 {len(gs.real_bullets) - gs.current_index} 發)")

    print(f"\nHP: You(P1)={gs.p1.hp} | AI(P2)={gs.p2.hp}\n")

    # 列出道具（格式化輸出）
    def item_str(items):
        return " | ".join(f"{k}:{v}" for k, v in vars(items).items())

    print("[Your Items]")
    print("  " + item_str(gs.p1.items))
    print("[AI Items]")
    print("  " + item_str(gs.p2.items))
    print("=" * 70)


# ================================
# 顯示編碼後的 state（debug 用）
# ================================
encoder_p2 = StateEncoderP2(max_bullets=8)


def show_state_encoding(gs: GameState):
    state_vec = encoder_p2.encode(gs)
    print("\n===== Encoded State (P2 view) =====")
    print(state_vec)
    print(f"Vector length = {len(state_vec)}")
    print("===================================\n")


# ================================
# 解析使用者指令（沿用 main.py）
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
# 人類 P1：使用道具（透過 env._use_item）
# ================================
def human_use_item(env: BuckshotEnv, gs: GameState, item: str):
    player = gs.p1
    opponent = gs.p2

    if item not in ITEM_LIST:
        print(f"未知道具：{item}")
        return

    if getattr(player.items, item, 0) <= 0:
        print(f"你沒有 {item}")
        return

    # 交給 BuckshotEnv 的 _use_item，內部會處理效果 + 扣道具
    _use_item(player, opponent, gs, item)
    print(f"你使用了 {item}")


# ================================
# 人類 P1：射擊（透過 env._shoot）
# ================================
def human_shoot(env: BuckshotEnv, gs: GameState, target: str):
    if target not in ("self", "enemy"):
        print("shoot 只能 self 或 enemy")
        return

    player = gs.p1
    opponent = gs.p2

    if gs.current_index >= len(gs.real_bullets):
        print("彈匣已空，將自動裝新一輪彈。")
        env._load_new_round()
        return

    victim = player if target == "self" else opponent

    print(f"你射擊了 {victim.name}（{'自己' if target == 'self' else 'AI'}）")
    env._shoot(gs, player, victim, target=target)


# ================================
# AI P2：完整一回合（item + shoot）
# ================================
def ai_take_turn(env: BuckshotEnv, model: MaskablePPO):
    gs = env.gs
    print("\n========== AI 的回合 ==========")

    # 如果 AI 被手銬，在 item phase 直接跳過
    if gs.p2.handcuffed and gs.phase == "item":
        print("AI 被手銬，這回合無法行動。")
        gs.p2.handcuffed = False
        gs.turn = "p1"
        gs.phase = "item"
        return

    # --------- AI 的 item phase ---------
    max_item_actions = 6
    items_used = 0

    while gs.phase == "item" and gs.turn == "p2" and items_used < max_item_actions:
        # 檢查彈匣是否打完
        if gs.current_index >= len(gs.real_bullets):
            print("AI：彈匣已空，重新裝彈。")
            env._load_new_round()
            # 新一輪可能輪到 P1 或 P2
            if gs.turn != "p2":
                return
            else:
                continue

        # 取得 action mask & obs (P2 視角)
        action_mask = env.action_masks()
        obs = env.encoder.encode(gs)
        action, _ = model.predict(obs, action_masks=action_mask, deterministic=False)

        ai_action_names = [
            "Shoot Enemy", "Shoot Self",
            "Use Magnifier", "Use Cigarette", "Use Beer",
            "Use Saw", "Use Handcuff", "Use Phone", "Use Reverse",
            "Ready"
        ]
        print(f"AI (item phase) 選擇動作: {ai_action_names[action]} (id={action})")

        if action == 9:
            # Ready -> 進入射擊階段
            show_state_encoding(gs)
            gs.phase = "shoot"
            break
        elif 2 <= action <= 8:
            # 使用道具
            show_state_encoding(gs)
            item_index = action - 2
            if 0 <= item_index < len(ITEM_LIST):
                item = ITEM_LIST[item_index]
                if getattr(gs.p2.items, item) > 0:
                    env._use_item(gs.p2, gs.p1, gs, item)
                    items_used += 1
                else:
                    # 沒有該道具 → 直接進入射擊階段
                    print(f"AI 試圖使用 {item} 但沒有，改為進入射擊階段。")
                    gs.phase = "shoot"
                    break
            else:
                gs.phase = "shoot"
                break
        else:
            # 其他在 item phase 不合法 → 直接切到射擊
            print("AI 在 item phase 選擇了不合法動作，進入射擊階段。")
            gs.phase = "shoot"
            break

    # --------- AI 的 shoot phase ---------
    if gs.phase == "shoot" and gs.turn == "p2":
        # 檢查子彈
        if gs.current_index >= len(gs.real_bullets):
            print("AI：彈匣已空，重新裝彈。")
            env._load_new_round()
            return

        action_mask = env.action_masks()
        obs = env.encoder.encode(gs)
        action, _ = model.predict(obs, action_masks=action_mask, deterministic=False)

        ai_action_names = [
            "Shoot Enemy", "Shoot Self",
            "Use Magnifier", "Use Cigarette", "Use Beer",
            "Use Saw", "Use Handcuff", "Use Phone", "Use Reverse",
            "Ready"
        ]
        print(f"AI (shoot phase) 選擇動作: {ai_action_names[action]} (id={action})")

        if action == 0:
            show_state_encoding(gs)
            print("AI 射擊了你！")
            env._shoot(gs, gs.p2, gs.p1, target="enemy")
        elif action == 1:
            show_state_encoding(gs)
            print("AI 射擊了自己！")
            env._shoot(gs, gs.p2, gs.p2, target="self")
        else:
            # 不合法就預設打你
            show_state_encoding(gs)
            print("AI 選擇了不合法射擊動作，預設射擊你。")
            env._shoot(gs, gs.p2, gs.p1, target="enemy")

        # 若子彈打完，重新裝一輪
        if gs.phase != "game_end" and gs.current_index >= len(gs.real_bullets):
            print("AI 行動後，彈匣用完，重新裝彈。")
            env._load_new_round()

    print("========== AI 回合結束 ==========\n")


# ================================
# 遊戲主迴圈：人類 P1 vs AI P2
# ================================
def play_against_ai(model_path: str):
    print("=" * 70)
    print("BUCKSHOT ROULETTE - Human (P1) vs AI (P2)")
    print("=" * 70)
    print(f"載入 AI 模型：{model_path}")

    model = MaskablePPO.load(model_path)
    print("✓ 模型載入完成！\n")

    # 建立環境（這裡不使用 env.reset()，避免 RL 版本的自動 P1 回合）
    env = BuckshotEnv(opponent_model=None)
    env.gs = GameState()         # 新遊戲狀態
    env._load_new_round()        # 用 buckshot_env 的規則裝彈 & 發道具
    gs = env.gs
    gs.turn = "p1"

    print("=" * 70)
    print("操作說明（跟 main.py 類似）：")
    print("  show             : 顯示完整遊戲狀態")
    print("  state            : 顯示 RL 狀態向量 (P2 視角)")
    print("  use <item>       : 使用道具，例如 use magnifier")
    print("                     道具名稱：magnifier / cigarette / beer / saw / handcuff / phone / reverse")
    print("  ready            : 結束道具階段，進入射擊階段")
    print("  shoot self       : 對自己開槍")
    print("  shoot enemy      : 對對方（AI）開槍")
    print("  help             : 再次顯示這個說明")
    print("=" * 70)
    input("\n按 Enter 開始遊戲...")

    # 主要迴圈
    while True:
        gs = env.gs

        # 檢查是否遊戲結束
        if gs.phase == "game_end" or gs.p1.hp <= 0 or gs.p2.hp <= 0:
            break

        # 人類 P1 的回合
        if gs.turn == "p1":
            # 手銬判定（跟 main.py 一樣）
            if gs.p1.handcuffed:
                print("你被手銬，這回合無法行動。")
                gs.p1.handcuffed = False
                gs.turn = "p2"
                gs.phase = "item"
                continue

            print(f"\n=== 你的回合（{gs.phase} phase）===")
            print(f"HP: 你={gs.p1.hp} | AI={gs.p2.hp}")
            print(f"子彈：live={gs.live_left}, blank={gs.blank_left}，尚餘 {len(gs.real_bullets) - gs.current_index} 發")

            # Item phase：使用道具或 ready
            if gs.phase == "item":
                command = input("[你] >> ").strip()
                args = parse_command(command)
                if args is None:
                    continue

                if args.action == "help":
                    print("可用指令：show / state / use <item> / ready / shoot <self|enemy>")
                    continue

                if args.action == "show":
                    show(gs)
                    continue

                if args.action == "state":
                    show_state_encoding(gs)
                    continue

                if args.action == "use":
                    human_use_item(env, gs, args.item)
                    continue

                if args.action == "ready":
                    gs.phase = "shoot"
                    continue

                # 在 item phase 輸入 shoot → 直接當成錯誤
                if args.action == "shoot":
                    print("現在是道具階段，請先 ready 再進入射擊階段。")
                    continue

            # Shoot phase：射擊
            if gs.phase == "shoot" and gs.turn == "p1":
                command = input("[你 - shoot] >> ").strip()
                args = parse_command(command)
                if args is None:
                    continue

                if args.action == "show":
                    show(gs)
                    continue

                if args.action == "state":
                    show_state_encoding(gs)
                    continue

                if args.action == "shoot":
                    human_shoot(env, gs, args.target)

                    # 檢查是否死亡
                    if gs.p1.hp <= 0 or gs.p2.hp <= 0 or gs.phase == "game_end":
                        break

                    # 子彈打完 → 下一輪
                    if gs.current_index >= len(gs.real_bullets):
                        print("\n=== 彈匣打空，開始下一輪 ===")
                        env._load_new_round()
                    else:
                        # 照 buckshot_env._shoot 的規則，phase 已被設為 item
                        pass

                    continue

                if args.action == "ready":
                    print("已經在射擊階段，不能再 ready。")
                    continue

                if args.action == "use":
                    print("射擊階段不能使用道具。請在道具階段使用 use。")
                    continue

        # AI P2 的回合
        elif gs.turn == "p2":
            ai_take_turn(env, model)
            input("（按 Enter 繼續）")

        else:
            # 理論上不會出現
            print(f"未知的 turn 狀態：{gs.turn}")
            break

    # 遊戲結束畫面
    print("\n" + "=" * 70)
    print("GAME OVER")
    print("=" * 70)
    print(f"最終 HP：你(P1)={gs.p1.hp} | AI(P2)={gs.p2.hp}")

    if gs.p1.hp > 0 and gs.p2.hp <= 0:
        print("\n🎉 你獲勝！")
    elif gs.p2.hp > 0 and gs.p1.hp <= 0:
        print("\n💀 AI 獲勝……")
    else:
        print("\n平手？（雙方都沒死或都死了）")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Play Buckshot Roulette against trained AI (Human=P1, AI=P2)")
    parser.add_argument("model", type=str, help="Path to trained model (e.g., models/buckshot_final.zip)")
    args = parser.parse_args()

    try:
        play_against_ai(args.model)
    except KeyboardInterrupt:
        print("\n\n遊戲中斷，再見！")
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()


