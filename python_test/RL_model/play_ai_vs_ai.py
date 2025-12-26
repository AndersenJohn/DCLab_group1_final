"""
AI vs AI - 讓兩個 AI 自己對打。

使用說明：
  python play_ai_vs_ai.py <model_p1_path> <model_p2_path> [--num_games N] [--verbose]

範例：
  python play_ai_vs_ai.py models/buckshot_final.zip models/buckshot_final.zip --num_games 10
"""

import argparse
import random
import numpy as np
from sb3_contrib import MaskablePPO

from buckshot_env import BuckshotEnv, ITEM_LIST
from game_state import GameState
from state_encoder_p1 import StateEncoder as StateEncoderP1  # P1 視角
from state_encoder_p2 import StateEncoder as StateEncoderP2  # P2 視角


def show_game_state(gs: GameState, verbose: bool = True):
    """顯示遊戲狀態"""
    if not verbose:
        return
    
    print(f"\n📊 Turn: {gs.turn.upper()} | Phase: {gs.phase}")
    print(f"   HP: P1={gs.p1.hp}  P2={gs.p2.hp}")
    print(f"   Bullets: live={gs.live_left}, blank={gs.blank_left} (remaining={len(gs.real_bullets) - gs.current_index})")


def ai_take_turn(env: BuckshotEnv, model: MaskablePPO, player_id: int, verbose: bool = True):
    """
    讓 AI 完整執行一回合（item phase + shoot phase）
    player_id: 1 for P1, 2 for P2
    """
    gs = env.gs
    player = gs.p1 if player_id == 1 else gs.p2
    opponent = gs.p2 if player_id == 1 else gs.p1
    
    player_name = "P1" if player_id == 1 else "P2"
    
    if verbose:
        print(f"\n{'=' * 50}")
        print(f"🤖 {player_name} 的回合開始")
        print(f"{'=' * 50}")
    
    # 檢查是否被手銬
    if player.handcuffed:
        if verbose:
            print(f"⛓️ {player_name} 被手銬，這回合無法行動。")
        player.handcuffed = False
        gs.turn = "p2" if player_id == 1 else "p1"
        gs.phase = "item"
        return
    
    # ===== Item Phase =====
    max_item_actions = 6
    items_used = 0
    
    while gs.phase == "item" and items_used < max_item_actions:
        # 檢查彈匣是否打完
        if gs.current_index >= len(gs.real_bullets):
            if verbose:
                print(f"{player_name}：彈匣已空，重新裝彈。")
            env._load_new_round()
            # 新一輪可能輪到對方
            if gs.turn != ("p1" if player_id == 1 else "p2"):
                return
            else:
                continue
        
        # 取得 action mask & obs
        action_mask = env.action_masks()
        
        if player_id == 1:
            encoder = StateEncoderP1(max_bullets=8)
            obs = encoder.encode(gs)
        else:
            encoder = StateEncoderP2(max_bullets=8)
            obs = encoder.encode(gs)
        
        action, _ = model.predict(obs, action_masks=action_mask, deterministic=False)
        
        ai_action_names = [
            "Shoot Enemy", "Shoot Self",
            "Magnifier", "Cigarette", "Beer",
            "Saw", "Handcuff", "Phone", "Reverse",
            "Ready"
        ]
        
        if verbose:
            print(f"  {player_name} (item) → {ai_action_names[action]} (id={action})")
        
        if action == 9:
            # Ready → 進入射擊階段
            gs.phase = "shoot"
            break
        elif 2 <= action <= 8:
            # 使用道具
            item_index = action - 2
            if 0 <= item_index < len(ITEM_LIST):
                item = ITEM_LIST[item_index]
                if getattr(player.items, item) > 0:
                    env._use_item(player, opponent, gs, item)
                    items_used += 1
                else:
                    if verbose:
                        print(f"     {player_name} 沒有 {item}，進入射擊階段。")
                    gs.phase = "shoot"
                    break
            else:
                gs.phase = "shoot"
                break
        else:
            # 不合法 → 進入射擊階段
            if verbose:
                print(f"     {player_name} 選擇不合法，進入射擊階段。")
            gs.phase = "shoot"
            break
    
    # ===== Shoot Phase =====
    if gs.phase == "shoot":
        # 檢查子彈
        if gs.current_index >= len(gs.real_bullets):
            if verbose:
                print(f"{player_name}：彈匣已空，重新裝彈。")
            env._load_new_round()
            return
        
        action_mask = env.action_masks()
        
        if player_id == 1:
            encoder = StateEncoderP1(max_bullets=8)
            obs = encoder.encode(gs)
        else:
            encoder = StateEncoderP2(max_bullets=8)
            obs = encoder.encode(gs)
        
        action, _ = model.predict(obs, action_masks=action_mask, deterministic=False)
        
        ai_action_names = [
            "Shoot Enemy", "Shoot Self",
            "Magnifier", "Cigarette", "Beer",
            "Saw", "Handcuff", "Phone", "Reverse",
            "Ready"
        ]
        
        if verbose:
            print(f"  {player_name} (shoot) → {ai_action_names[action]} (id={action})")
        
        if action == 0:
            target = "enemy"
            if verbose:
                print(f"  💥 {player_name} 射擊對手")
            env._shoot(gs, player, opponent, target=target)
        elif action == 1:
            target = "self"
            if verbose:
                print(f"  💥 {player_name} 對自己開槍")
            env._shoot(gs, player, player, target=target)
        else:
            # 不合法就射對手
            target = "enemy"
            if verbose:
                print(f"  💥 {player_name} 選擇不合法，預設射擊對手")
            env._shoot(gs, player, opponent, target=target)
        
        # 子彈打完 → 下一輪
        if gs.phase != "game_end" and gs.current_index >= len(gs.real_bullets):
            if verbose:
                print(f"  {player_name} 行動後，彈匣用完，重新裝彈。")
            env._load_new_round()
    
    if verbose:
        print(f"{'=' * 50}\n")


def play_ai_vs_ai(model_p1_path: str, model_p2_path: str, num_games: int = 1, verbose: bool = True):
    """執行 AI vs AI 對戰"""
    
    print("\n" + "=" * 70)
    print("BUCKSHOT ROULETTE - AI (P1) vs AI (P2)")
    print("=" * 70)
    print(f"P1 模型：{model_p1_path}")
    print(f"P2 模型：{model_p2_path}")
    print(f"遊戲數：{num_games}")
    print(f"詳細模式：{'開啟' if verbose else '關閉'}")
    print("=" * 70 + "\n")
    
    # 載入模型
    print("載入 AI 模型...")
    model_p1 = MaskablePPO.load(model_p1_path)
    model_p2 = MaskablePPO.load(model_p2_path)
    print("✓ 模型載入完成！\n")
    
    # 統計
    p1_wins = 0
    p2_wins = 0
    draws = 0
    
    # 進行多場遊戲
    for game_num in range(num_games):
        print(f"\n{'#' * 70}")
        print(f"  第 {game_num + 1} 局 / {num_games}")
        print(f"{'#' * 70}\n")
        
        # 建立新環境
        env = BuckshotEnv(opponent_model=None)
        env.gs = GameState()
        env._load_new_round()
        gs = env.gs
        gs.turn = "p1"
        
        turn_count = 0
        max_turns = 100  # 避免無限迴圈
        
        # 遊戲主迴圈
        while turn_count < max_turns:
            gs = env.gs
            
            # 檢查是否遊戲結束
            if gs.phase == "game_end" or gs.p1.hp <= 0 or gs.p2.hp <= 0:
                break
            
            show_game_state(gs, verbose)
            
            # P1 的回合
            if gs.turn == "p1":
                ai_take_turn(env, model_p1, player_id=1, verbose=verbose)
                turn_count += 1
            
            # P2 的回合
            elif gs.turn == "p2":
                ai_take_turn(env, model_p2, player_id=2, verbose=verbose)
                turn_count += 1
            
            else:
                print(f"未知的 turn 狀態：{gs.turn}")
                break
        
        # 判斷勝敗
        print("\n" + "=" * 70)
        print("🏁 本局結束")
        print("=" * 70)
        print(f"最終 HP：P1={gs.p1.hp} | P2={gs.p2.hp}")
        
        if gs.p1.hp > 0 and gs.p2.hp <= 0:
            print("\n✅ P1 獲勝！")
            p1_wins += 1
        elif gs.p2.hp > 0 and gs.p1.hp <= 0:
            print("\n✅ P2 獲勝！")
            p2_wins += 1
        else:
            print("\n🤝 平手")
            draws += 1
        
        print("=" * 70 + "\n")
    
    # 顯示統計
    print("\n" + "=" * 70)
    print("📊 統計結果")
    print("=" * 70)
    print(f"總遊戲數：{num_games}")
    print(f"P1 勝利：{p1_wins} ({100*p1_wins/num_games:.1f}%)")
    print(f"P2 勝利：{p2_wins} ({100*p2_wins/num_games:.1f}%)")
    print(f"平手：{draws} ({100*draws/num_games:.1f}%)")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="AI vs AI - 讓兩個 AI 模型互相對戰"
    )
    parser.add_argument("model_p1", type=str, help="P1 的模型路徑")
    parser.add_argument("model_p2", type=str, help="P2 的模型路徑")
    parser.add_argument(
        "--num_games", "-n",
        type=int,
        default=1,
        help="進行的遊戲數（預設為 1）"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="顯示詳細訊息"
    )
    
    args = parser.parse_args()
    
    try:
        play_ai_vs_ai(
            args.model_p1,
            args.model_p2,
            num_games=args.num_games,
            verbose=args.verbose
        )
    except KeyboardInterrupt:
        print("\n\n🛑 遊戲中斷，再見！")
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
