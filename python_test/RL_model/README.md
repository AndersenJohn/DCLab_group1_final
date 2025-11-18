# Buckshot Roulette RL Training

Reinforcement Learning agent for Buckshot Roulette using self-play with MaskablePPO.

## Setup

```bash
pip install -r requirements.txt
```

## Quick Start

### Train a New Model
```bash
python train.py --train
```

### Train with Custom Settings
```bash
python train.py --train --timesteps 2000000 --n-envs 8 --lr 0.0003
```

### Evaluate Trained Model
```bash
python train.py --eval models/buckshot_final
```

## Model Architecture

- **Algorithm**: MaskablePPO (Proximal Policy Optimization with action masking)
- **Network**: MLP [Input(30) → Hidden(128) → Hidden(128) → Output(9)]
- **Parameters**: ~21,000 trainable parameters
- **Input**: 30-dimensional state vector
  - Global info (4): live_left, blank_left, current_index, saw_active
  - Phase (2): one-hot encoding
  - Self info (8): HP, handcuffed, 6 items
  - Opponent info (8): HP, handcuffed, 6 items
  - Bullet knowledge (8): known bullet types
- **Output**: 9 discrete actions (0-8)
  - 0: Shoot enemy
  - 1: Shoot self
  - 2-7: Use items (magnifier, cigarette, beer, saw, handcuff, phone)
  - 8: Ready (transition to shoot phase)

## Training Features

- ✅ **Self-play**: Agent plays against itself
- ✅ **Action masking**: Invalid actions automatically blocked
- ✅ **Opponent updates**: Opponent model updated every 10k steps
- ✅ **Metrics tracking**: Win rate, avg reward, episode length
- ✅ **Tensorboard logging**: Visualize training progress
- ✅ **Auto-save**: Models saved periodically

## File Structure

```
RL_model/
├── game_state.py          # Game state dataclasses
├── state_encoder_p1.py    # P1 state encoder
├── state_encoder_p2.py    # P2 state encoder
├── buckshot_env.py        # Gym environment
├── train.py               # Training script
├── requirements.txt       # Dependencies
└── README.md             # This file
```

## Monitoring Training

### View Tensorboard
```bash
tensorboard --logdir logs/
```

### Training Output
- Real-time win rate and metrics
- Opponent update notifications
- Progress bar with ETA

## Hyperparameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `total_timesteps` | 1,000,000 | Total training steps |
| `n_envs` | 4 | Parallel environments |
| `learning_rate` | 3e-4 | Learning rate |
| `batch_size` | 64 | Batch size for updates |
| `n_steps` | 2048 | Steps per environment before update |
| `opponent_update_freq` | 10,000 | Steps between opponent updates |

## Expected Training Time

- **1M timesteps**: ~30-60 minutes (4 parallel envs)
- **Win rate**: Should reach >40% against self by 500k steps
- **Convergence**: ~1-2M timesteps for strong play

## Troubleshooting

**Issue**: ImportError for sb3_contrib
```bash
pip install sb3-contrib
```

**Issue**: Slow training
- Increase `n_envs` (e.g., 8 or 16)
- Reduce `n_steps` (e.g., 1024)

**Issue**: Unstable training
- Decrease `learning_rate` (e.g., 1e-4)
- Increase `opponent_update_freq` (e.g., 20000)
