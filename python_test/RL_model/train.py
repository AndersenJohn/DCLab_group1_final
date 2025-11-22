"""
Buckshot Roulette RL Training Script
Self-play implementation using MaskablePPO from Stable-Baselines3
"""

import os
import numpy as np
import torch
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.monitor import Monitor
from sb3_contrib import MaskablePPO
from buckshot_env import BuckshotEnv


class SelfPlayCallback(BaseCallback):
    """
    Callback to update opponent model periodically during self-play training
    """
    def __init__(self, update_freq=10000, metrics_callback=None, verbose=1):
        super().__init__(verbose)
        self.update_freq = update_freq
        self.opponent_update_count = 0
        self.metrics_callback = metrics_callback

    def _on_step(self) -> bool:
        # Update opponent every update_freq steps
        if self.n_calls % self.update_freq == 0:
            # Show interval stats before updating
            if self.metrics_callback and self.verbose > 0:
                self.metrics_callback.print_interval_stats(self.opponent_update_count)

            if self.verbose > 0:
                print(f"\n{'='*60}")
                print(f"Updating opponent model at step {self.n_calls}")
                print(f"Opponent update count: {self.opponent_update_count + 1}")
                print(f"{'='*60}\n")

            # Update opponent to current policy
            for env in self.training_env.envs:
                env.opponent_model = self.model

            self.opponent_update_count += 1

            # Reset interval counters
            if self.metrics_callback:
                self.metrics_callback.reset_interval()

        return True


class MetricsCallback(BaseCallback):
    """
    Track game metrics like win rate, episode length, rewards
    """
    def __init__(self, check_freq=1000, verbose=1):
        super().__init__(verbose)
        self.check_freq = check_freq
        self.episode_rewards = []
        self.episode_lengths = []

        # Cumulative stats (across all training)
        self.wins = 0
        self.losses = 0

        # Interval stats (reset when opponent is updated)
        self.interval_wins = 0
        self.interval_losses = 0

    def reset_interval(self):
        """Reset interval counters when opponent is updated"""
        self.interval_wins = 0
        self.interval_losses = 0

    def print_interval_stats(self, interval_num):
        """Print statistics for the current interval before resetting"""
        interval_games = self.interval_wins + self.interval_losses
        if interval_games > 0:
            interval_wr = self.interval_wins / interval_games
            print(f"\n{'='*60}")
            print(f"INTERVAL {interval_num} SUMMARY (vs frozen opponent)")
            print(f"{'='*60}")
            print(f"Interval Win Rate: {interval_wr:.2%} ({self.interval_wins}W / {self.interval_losses}L)")
            print(f"Games Played: {interval_games}")
            print(f"{'='*60}")

    def _on_step(self) -> bool:
        # Check done episodes
        for idx, done in enumerate(self.locals['dones']):
            if done:
                # Get episode info
                info = self.locals['infos'][idx]

                # Track episode reward
                if 'episode' in info:
                    ep_reward = info['episode']['r']
                    ep_length = info['episode']['l']
                    self.episode_rewards.append(ep_reward)
                    self.episode_lengths.append(ep_length)

                    # Track wins/losses (positive terminal reward = win)
                    is_win = ep_reward > 5  # Win gives +10 + other rewards

                    # Update cumulative stats
                    if is_win:
                        self.wins += 1
                        self.interval_wins += 1
                    else:
                        self.losses += 1
                        self.interval_losses += 1

        # Log metrics periodically
        if self.n_calls % self.check_freq == 0 and len(self.episode_rewards) > 0:
            total_games = self.wins + self.losses
            cumulative_wr = self.wins / total_games if total_games > 0 else 0

            interval_games = self.interval_wins + self.interval_losses
            interval_wr = self.interval_wins / interval_games if interval_games > 0 else 0

            avg_reward = np.mean(self.episode_rewards[-100:])
            avg_length = np.mean(self.episode_lengths[-100:])

            print(f"\n{'='*60}")
            print(f"Step: {self.n_calls}")
            print(f"Cumulative Win Rate: {cumulative_wr:.2%} ({self.wins}W / {self.losses}L)")
            print(f"Current Interval Win Rate: {interval_wr:.2%} ({self.interval_wins}W / {self.interval_losses}L)")
            print(f"Avg Reward (last 100): {avg_reward:.2f}")
            print(f"Avg Episode Length (last 100): {avg_length:.1f}")
            print(f"{'='*60}\n")

        return True


def make_env():
    """Create a single environment instance"""
    env = BuckshotEnv()
    env = Monitor(env)
    return env


def train(
    total_timesteps=1_000_000,
    n_envs=4,
    learning_rate=3e-4,
    batch_size=256,
    n_steps=2048,
    n_epochs=10,
    opponent_update_freq=10000,
    save_freq=50000,
    model_dir="models",
    log_dir="logs"
):
    """
    Train Buckshot Roulette agent with self-play

    Args:
        total_timesteps: Total training steps
        n_envs: Number of parallel environments
        learning_rate: Learning rate for PPO
        batch_size: Batch size for training
        n_steps: Steps per environment before update
        n_epochs: Number of epochs per update
        opponent_update_freq: Steps between opponent updates
        save_freq: Steps between model saves
        model_dir: Directory to save models
        log_dir: Directory for tensorboard logs
    """

    # Create directories
    os.makedirs(model_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)

    # Check GPU availability
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f"\n🚀 GPU detected: {gpu_name} ({gpu_memory:.1f} GB)")
        print(f"   CUDA version: {torch.version.cuda}")
        print(f"   Training device: {device}")
    else:
        print(f"\n⚠️  No GPU detected, using CPU")
        print(f"   Training device: {device}")
        print(f"   Consider installing CUDA for faster training")

    print("\n" + "="*60)
    print("Buckshot Roulette Self-Play Training")
    print("="*60)
    print(f"Total timesteps: {total_timesteps:,}")
    print(f"Parallel envs: {n_envs}")
    print(f"Learning rate: {learning_rate}")
    print(f"Batch size: {batch_size}")
    print(f"Steps per update: {n_steps}")
    print(f"Opponent update freq: {opponent_update_freq:,}")
    print("="*60 + "\n")

    # Create vectorized environment (no opponent initially)
    from stable_baselines3.common.vec_env import DummyVecEnv
    env = DummyVecEnv([make_env for _ in range(n_envs)])

    # Create model with custom MLP architecture
    print("Creating MaskablePPO model with MLP architecture [128, 128]...")
    model = MaskablePPO(
        "MlpPolicy",
        env,
        policy_kwargs=dict(
            net_arch=[128, 128],  # Two hidden layers: 30 → 128 → 128 → 9
            activation_fn=torch.nn.ReLU  # Change from default Tanh to ReLU
        ),
        learning_rate=learning_rate,
        n_steps=n_steps,
        batch_size=batch_size,
        n_epochs=n_epochs,
        gamma=0.99,           # Discount factor
        gae_lambda=0.95,      # GAE lambda
        clip_range=0.2,       # PPO clip range
        ent_coef=0.01,        # Entropy coefficient (encourage exploration)
        verbose=1,
        tensorboard_log=None,
        device=device         # Use GPU if available, otherwise CPU
    )

    print(f"Model created! Total parameters: ~21,000")
    print(f"Network: Input(30) → Hidden(128) → Hidden(128) → Output(9)\n")

    # Initialize opponent model in all environments (important for self-play to work from start)
    print("Initializing opponent model in all environments...")
    for i in range(n_envs):
        env.env_method("__setattr__", "opponent_model", model, indices=[i])
    print(f"✓ Opponent model set in {n_envs} environments\n")

    # Create callbacks
    metrics_callback = MetricsCallback(
        check_freq=1000,
        verbose=1
    )

    selfplay_callback = SelfPlayCallback(
        update_freq=opponent_update_freq,
        metrics_callback=metrics_callback,
        verbose=1
    )

    # Start training
    print("Starting training...\n")

    try:
        model.learn(
            total_timesteps=total_timesteps,
            callback=[selfplay_callback, metrics_callback],
            progress_bar=True
        )

        # Save final model
        final_path = os.path.join(model_dir, "buckshot_final")
        model.save(final_path)
        print(f"\n✅ Training complete! Model saved to {final_path}")

    except KeyboardInterrupt:
        print("\n⚠️  Training interrupted by user")
        interrupt_path = os.path.join(model_dir, "buckshot_interrupted")
        model.save(interrupt_path)
        print(f"Model saved to {interrupt_path}")

    env.close()
    return model


def evaluate(model_path, n_episodes=100):
    """
    Evaluate trained model

    Args:
        model_path: Path to saved model
        n_episodes: Number of episodes to evaluate
    """
    print(f"\n{'='*60}")
    print(f"Evaluating model: {model_path}")
    print(f"Episodes: {n_episodes}")
    print(f"{'='*60}\n")

    # Load model
    model = MaskablePPO.load(model_path)

    # Create environment with self-play
    env = BuckshotEnv(opponent_model=model)

    wins = 0
    total_reward = 0
    episode_lengths = []

    for episode in range(n_episodes):
        obs, _ = env.reset()
        done = False
        ep_reward = 0
        ep_length = 0

        while not done:
            # Get action mask
            action_mask = env.action_masks()

            # Predict action
            action, _ = model.predict(obs, action_masks=action_mask, deterministic=True)

            # Step environment
            obs, reward, done, truncated, info = env.step(action)
            ep_reward += reward
            ep_length += 1

        total_reward += ep_reward
        episode_lengths.append(ep_length)

        if ep_reward > 5:  # Win
            wins += 1
            result = "WIN"
        else:
            result = "LOSS"

        if (episode + 1) % 10 == 0:
            print(f"Episode {episode + 1}/{n_episodes}: {result} | Reward: {ep_reward:.2f} | Length: {ep_length}")

    # Print summary
    win_rate = wins / n_episodes
    avg_reward = total_reward / n_episodes
    avg_length = np.mean(episode_lengths)

    print(f"\n{'='*60}")
    print(f"Evaluation Results")
    print(f"{'='*60}")
    print(f"Win Rate: {win_rate:.2%} ({wins}/{n_episodes})")
    print(f"Avg Reward: {avg_reward:.2f}")
    print(f"Avg Episode Length: {avg_length:.1f}")
    print(f"{'='*60}\n")

    env.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Train Buckshot Roulette RL Agent")
    parser.add_argument("--train", action="store_true", help="Train a new model")
    parser.add_argument("--eval", type=str, help="Evaluate a trained model (provide path)")
    parser.add_argument("--timesteps", type=int, default=1_000_000, help="Total training timesteps")
    parser.add_argument("--n-envs", type=int, default=4, help="Number of parallel environments")
    parser.add_argument("--lr", type=float, default=3e-4, help="Learning rate")

    args = parser.parse_args()

    if args.train:
        train(
            total_timesteps=args.timesteps,
            n_envs=args.n_envs,
            learning_rate=args.lr
        )
    elif args.eval:
        evaluate(args.eval, n_episodes=100)
    else:
        print("Usage:")
        print("  Train: python train.py --train")
        print("  Train with custom settings: python train.py --train --timesteps 2000000 --n-envs 8")
        print("  Evaluate: python train.py --eval models/buckshot_final")
