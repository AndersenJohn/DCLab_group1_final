"""
Watch a trained model play Buckshot Roulette
Shows detailed game state and model decisions
"""

import time
from sb3_contrib import MaskablePPO
from buckshot_env import BuckshotEnv


def watch_game(model_path, num_games=5, delay=0.5):
    """
    Watch the trained model play games with detailed output

    Args:
        model_path: Path to saved model
        num_games: Number of games to watch
        delay: Delay between actions (seconds)
    """
    print("="*70)
    print(f"Loading model: {model_path}")
    print("="*70)

    # Load trained model
    model = MaskablePPO.load(model_path)

    # Create environment with self-play and verbose mode to see P1's actions
    env = BuckshotEnv(opponent_model=model, verbose=True)

    action_names = [
        "Shoot Enemy", "Shoot Self",
        "Use Magnifier", "Use Cigarette", "Use Beer",
        "Use Saw", "Use Handcuff", "Use Phone",
        "Ready (End Item Phase)"
    ]

    wins = 0

    for game_num in range(num_games):
        print(f"\n{'='*70}")
        print(f"GAME {game_num + 1}/{num_games}")
        print(f"{'='*70}\n")

        obs, _ = env.reset()
        done = False
        step = 0

        while not done:
            gs = env.gs

            # Show game state
            print(f"\n--- Step {step} ---")
            print(f"Turn: {'P2 (Agent)' if gs.turn == 'p2' else 'P1 (Opponent)'} | Phase: {gs.phase.upper()}")
            print(f"P1 HP: {gs.p1.hp} | P2 HP: {gs.p2.hp}")

            # Show bullets
            bullets_left = len(gs.real_bullets) - gs.current_index
            print(f"Bullets: {gs.live_left} live, {gs.blank_left} blank ({bullets_left} total)")

            # Show items (P2 only)
            if gs.turn == "p2":
                items_p2 = gs.p2.items
                items_str = f"Items: Mag:{items_p2.magnifier} Cig:{items_p2.cigarette} " \
                           f"Beer:{items_p2.beer} Saw:{items_p2.saw} Cuff:{items_p2.handcuff} " \
                           f"Phone:{items_p2.phone}"
                print(items_str)

                # Show knowledge
                known_bullets = sum(1 for b in gs.p2.bullet_knowledge if b is not None)
                if known_bullets > 0:
                    knowledge_str = "Known: " + ", ".join(
                        f"#{i}={b}" for i, b in enumerate(gs.p2.bullet_knowledge)
                        if b is not None
                    )
                    print(knowledge_str)

                # Get and display action
                action_mask = env.action_masks()
                action, _ = model.predict(obs, action_masks=action_mask, deterministic=False)

                print(f"→ P2 Action: {action_names[action]}")

                # Take action
                obs, reward, done, truncated, info = env.step(action)

                if reward != 0:
                    print(f"  Reward: {reward:+.2f}")
            else:
                # P1's turn happens inside env.step() or reset()
                # We just need to call step() once to advance
                print("→ P1 (Opponent) taking turn...")
                action_mask = env.action_masks()
                action, _ = model.predict(obs, action_masks=action_mask, deterministic=False)
                obs, reward, done, truncated, info = env.step(action)

            step += 1
            time.sleep(delay)

            # Check if game ended
            if done:
                print(f"\n{'='*70}")
                if gs.p2.hp > 0 and gs.p1.hp <= 0:
                    print("🎉 P2 (Agent) WINS!")
                    wins += 1
                else:
                    print("💀 P1 (Opponent) WINS!")
                print(f"Game lasted {step} steps")
                print(f"{'='*70}")

        # Pause between games
        if game_num < num_games - 1:
            print("\n(Press Ctrl+C to stop, or wait for next game...)")
            time.sleep(2)

    # Final summary
    print(f"\n{'='*70}")
    print(f"SUMMARY: {wins}/{num_games} wins ({wins/num_games*100:.1f}%)")
    print(f"{'='*70}\n")

    env.close()


def quick_evaluation(model_path, num_games=100):
    """
    Quick evaluation without detailed output

    Args:
        model_path: Path to saved model
        num_games: Number of games to evaluate
    """
    print(f"\nEvaluating {model_path} over {num_games} games...\n")

    model = MaskablePPO.load(model_path)
    env = BuckshotEnv(opponent_model=model)

    wins = 0
    total_reward = 0
    total_steps = 0

    for game in range(num_games):
        obs, _ = env.reset()
        done = False
        ep_reward = 0
        ep_steps = 0

        while not done:
            action_mask = env.action_masks()
            action, _ = model.predict(obs, action_masks=action_mask, deterministic=True)
            obs, reward, done, truncated, info = env.step(action)
            ep_reward += reward
            ep_steps += 1

        if env.gs.p2.hp > 0 and env.gs.p1.hp <= 0:
            wins += 1
            result = "W"
        else:
            result = "L"

        total_reward += ep_reward
        total_steps += ep_steps

        if (game + 1) % 10 == 0:
            print(f"Game {game+1:3d}: {result} | Reward: {ep_reward:+6.2f} | Steps: {ep_steps:3d}")

    print(f"\n{'='*70}")
    print(f"Win Rate: {wins/num_games*100:.1f}% ({wins}/{num_games})")
    print(f"Avg Reward: {total_reward/num_games:.2f}")
    print(f"Avg Steps: {total_steps/num_games:.1f}")
    print(f"{'='*70}\n")

    env.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Watch trained Buckshot Roulette model play")
    parser.add_argument("model", type=str, help="Path to saved model (e.g., models/buckshot_final)")
    parser.add_argument("--games", type=int, default=5, help="Number of games to watch")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between actions (seconds)")
    parser.add_argument("--quick", action="store_true", help="Quick evaluation mode (no details)")
    parser.add_argument("--eval-games", type=int, default=100, help="Games for quick eval")

    args = parser.parse_args()

    if args.quick:
        quick_evaluation(args.model, args.eval_games)
    else:
        watch_game(args.model, args.games, args.delay)
