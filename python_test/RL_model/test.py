"""
Simple test script for BuckshotEnv
Tests the environment with random actions to verify it works correctly
No ML libraries needed - just tests game logic
"""

import numpy as np
import random
from buckshot_env import BuckshotEnv


def test_environment(num_episodes=10, max_steps_per_episode=200, verbose=True):
    """
    Test the environment with random valid actions

    Args:
        num_episodes: Number of games to play
        max_steps_per_episode: Maximum steps per episode
        verbose: Print detailed info
    """
    print("="*60)
    print("Testing Buckshot Roulette Environment")
    print("="*60)

    env = BuckshotEnv(opponent_model=None)  # No opponent model - uses random actions
    # Sanity check: action space should match buckshot_env (10 actions: 0..9)
    assert env.action_space.n == 10, f"Expected env.action_space.n == 10, got {env.action_space.n}"

    total_steps = 0
    wins = 0
    losses = 0
    crashes = 0

    for episode in range(num_episodes):
        if verbose:
            print(f"\n{'='*60}")
            print(f"Episode {episode + 1}/{num_episodes}")
            print(f"{'='*60}")

        try:
            obs, info = env.reset()
            done = False
            step_count = 0
            episode_reward = 0

            while not done and step_count < max_steps_per_episode:
                # Get valid actions from action mask
                action_mask = env.action_masks()

                # Verify mask has at least one valid action
                if action_mask.sum() == 0:
                    print(f"❌ ERROR: All actions masked at step {step_count}!")
                    print(f"   Phase: {env.gs.phase}, Turn: {env.gs.turn}")
                    print(f"   P1 HP: {env.gs.p1.hp}, P2 HP: {env.gs.p2.hp}")
                    crashes += 1
                    break

                # Choose random valid action
                valid_actions = np.where(action_mask == 1)[0]
                action = random.choice(valid_actions)

                if verbose:
                    phase = env.gs.phase
                    turn = env.gs.turn
                    p1_hp = env.gs.p1.hp
                    p2_hp = env.gs.p2.hp
                    bullets_left = len(env.gs.real_bullets) - env.gs.current_index

                    action_names = [
                        "shoot_enemy", "shoot_self",
                        "magnifier", "cigarette", "beer", "saw", "handcuff", "phone",
                        "reverse", "ready"
                    ]

                    print(f"Step {step_count:3d} | Phase: {phase:5s} | Turn: {turn} | " +
                          f"P1: {p1_hp}HP | P2: {p2_hp}HP | Bullets: {bullets_left} | " +
                          f"Action: {action_names[action]:12s}")

                # Take action
                obs, reward, done, truncated, info = env.step(action)
                episode_reward += reward
                step_count += 1

                # Check for errors
                if env.gs.current_index > len(env.gs.real_bullets):
                    print(f"❌ ERROR: Bullet index out of range!")
                    crashes += 1
                    break

            # Episode finished
            if done:
                if env.gs.p2.hp > 0 and env.gs.p1.hp <= 0:
                    result = "WIN"
                    wins += 1
                    emoji = "✅"
                else:
                    result = "LOSS"
                    losses += 1
                    emoji = "❌"

                total_steps += step_count

                if verbose:
                    print(f"\n{emoji} Episode {episode + 1} finished: {result}")
                    print(f"   Steps: {step_count}, Reward: {episode_reward:.2f}")
                    print(f"   Final HP - P1: {env.gs.p1.hp}, P2: {env.gs.p2.hp}")
                else:
                    print(f"Episode {episode + 1:2d}: {result:4s} | Steps: {step_count:3d} | Reward: {episode_reward:6.2f}")
            else:
                print(f"⚠️  Episode {episode + 1} reached max steps ({max_steps_per_episode})")

        except Exception as e:
            print(f"\n❌ CRASH in episode {episode + 1}: {type(e).__name__}: {e}")
            crashes += 1
            import traceback
            traceback.print_exc()

    # Print summary
    print(f"\n{'='*60}")
    print(f"Test Summary")
    print(f"{'='*60}")
    print(f"Episodes completed: {num_episodes}")
    print(f"Wins:   {wins:3d} ({wins/num_episodes*100:.1f}%)")
    print(f"Losses: {losses:3d} ({losses/num_episodes*100:.1f}%)")
    print(f"Crashes: {crashes:3d}")
    print(f"Avg steps per episode: {total_steps / max(1, wins + losses):.1f}")

    if crashes == 0:
        print(f"\n✅ All tests passed! Environment is working correctly.")
    else:
        print(f"\n❌ {crashes} crashes detected. Environment has bugs.")

    print(f"{'='*60}\n")

    env.close()
    return crashes == 0


def quick_test():
    """Quick test with minimal output"""
    print("Running quick test (5 episodes)...")
    return test_environment(num_episodes=5, verbose=False)


def thorough_test():
    """Thorough test with detailed output"""
    print("Running thorough test (20 episodes)...")
    return test_environment(num_episodes=20, verbose=False)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test Buckshot Roulette Environment")
    parser.add_argument("--quick", action="store_true", help="Quick test (5 episodes)")
    parser.add_argument("--thorough", action="store_true", help="Thorough test (20 episodes)")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--episodes", type=int, default=100, help="Number of episodes")

    args = parser.parse_args()

    if args.quick:
        success = quick_test()
    elif args.thorough:
        success = thorough_test()
    else:
        success = test_environment(num_episodes=args.episodes, verbose=args.verbose)

    exit(0 if success else 1)
