"""
Pure PyTorch implementation of the MaskablePPO model
Can load weights from Stable-Baselines3 checkpoints
"""
import torch
import torch.nn as nn
import numpy as np
from sb3_contrib import MaskablePPO


class BuckshotActorCritic(nn.Module):
    """
    Pure PyTorch implementation matching SB3's MaskableActorCriticPolicy
    Simplified to actor-only model (policy network only, no critic)

    Architecture:
    - Input: 30 features (game state)
    - Actor Network: 30 → 128 → 128 → 9 (action logits)
    """

    def __init__(self):
        super().__init__()

        # Actor Network (Policy Network) - decides actions
        self.policy_net = nn.Sequential(
            nn.Linear(30, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU()
        )

        # Action head - outputs action logits
        self.action_head = nn.Linear(128, 9)

    def forward(self, state):
        """
        Forward pass through the network

        Args:
            state: (batch_size, 30) tensor of game state

        Returns:
            action_logits: (batch_size, 9) raw scores for each action
        """
        # Process through actor network
        policy_features = self.policy_net(state)
        action_logits = self.action_head(policy_features)
        return action_logits

    def get_action(self, state, action_mask=None, deterministic=False):
        """
        Get action from the model (like SB3's predict)

        Args:
            state: (30,) numpy array of game state
            action_mask: (9,) binary mask (1=valid, 0=invalid)
            deterministic: If True, pick best action; if False, sample

        Returns:
            action: Integer action (0-8)
        """
        # Convert to tensor
        state_tensor = torch.FloatTensor(state).unsqueeze(0)  # Add batch dim

        with torch.no_grad():
            action_logits = self.forward(state_tensor)
            action_logits = action_logits.squeeze(0)  # Remove batch dim

            # Apply action mask if provided
            if action_mask is not None:
                # Set invalid actions to very negative number
                mask = torch.FloatTensor(action_mask)
                action_logits = torch.where(
                    mask == 1,
                    action_logits,
                    torch.tensor(-1e8)
                )

            # Get action
            if deterministic:
                action = torch.argmax(action_logits).item()
            else:
                # Sample from softmax distribution
                probs = torch.softmax(action_logits, dim=0)
                action = torch.multinomial(probs, 1).item()

        return action

    def load_from_sb3(self, sb3_model_path):
        """
        Load weights from Stable-Baselines3 checkpoint (actor only)

        Args:
            sb3_model_path: Path to .zip file (without .zip extension)
        """
        # Load SB3 model
        sb3_model = MaskablePPO.load(sb3_model_path)
        sb3_policy = sb3_model.policy

        # Map SB3 weights to our model (actor only)
        state_dict = {}

        # Policy network (actor)
        state_dict['policy_net.0.weight'] = sb3_policy.mlp_extractor.policy_net[0].weight
        state_dict['policy_net.0.bias'] = sb3_policy.mlp_extractor.policy_net[0].bias
        state_dict['policy_net.2.weight'] = sb3_policy.mlp_extractor.policy_net[2].weight
        state_dict['policy_net.2.bias'] = sb3_policy.mlp_extractor.policy_net[2].bias

        # Action head
        state_dict['action_head.weight'] = sb3_policy.action_net.weight
        state_dict['action_head.bias'] = sb3_policy.action_net.bias

        # Load into our model
        self.load_state_dict(state_dict)
        print(f"✓ Successfully loaded actor weights from {sb3_model_path}.zip")


def compare_outputs():
    """
    Compare outputs between SB3 model and pure PyTorch model
    """
    print("=" * 80)
    print("COMPARING SB3 MODEL vs PURE PYTORCH MODEL")
    print("=" * 80)

    # Load SB3 model
    sb3_model = MaskablePPO.load("buckshot_final")

    # Create and load PyTorch model
    pytorch_model = BuckshotActorCritic()
    pytorch_model.load_from_sb3("buckshot_final")
    pytorch_model.eval()

    # Create random test input
    test_state = np.random.randn(30).astype(np.float32)
    test_mask = np.array([1, 1, 0, 0, 0, 1, 0, 0, 1], dtype=np.int8)

    print("\nTest Input:")
    print(f"  State shape: {test_state.shape}")
    print(f"  Action mask: {test_mask}")

    # Get SB3 output
    sb3_action, _ = sb3_model.predict(test_state, action_masks=test_mask, deterministic=True)

    # Get PyTorch output
    pytorch_action = pytorch_model.get_action(test_state, action_mask=test_mask, deterministic=True)

    print("\nOutputs:")
    print(f"  SB3 action:     {sb3_action}")
    print(f"  PyTorch action: {pytorch_action}")

    if sb3_action == pytorch_action:
        print("\n✓ SUCCESS! Both models produce the same output!")
    else:
        print("\n✗ WARNING: Outputs differ!")

    # Get full forward pass outputs
    state_tensor = torch.FloatTensor(test_state).unsqueeze(0)

    with torch.no_grad():
        # PyTorch model
        pt_logits = pytorch_model(state_tensor)

        # SB3 model (extract from policy)
        features = sb3_model.policy.extract_features(state_tensor)
        latent_pi, _ = sb3_model.policy.mlp_extractor(features)
        sb3_logits = sb3_model.policy.action_net(latent_pi)

    print("\nDetailed comparison:")
    print(f"  Action logits difference: {torch.max(torch.abs(pt_logits - sb3_logits)).item():.6f}")

    print("\n" + "=" * 80)


def example_usage():
    """
    Show how to use the pure PyTorch model
    """
    print("\n" + "=" * 80)
    print("EXAMPLE USAGE")
    print("=" * 80)

    # Create model
    model = BuckshotActorCritic()

    # Load weights from checkpoint
    model.load_from_sb3("buckshot_final")
    model.eval()  # Set to evaluation mode

    # Example game state (30 numbers)
    state = np.random.randn(30).astype(np.float32)
    action_mask = np.array([1, 1, 0, 0, 0, 0, 0, 0, 1], dtype=np.int8)

    print("\nGetting action from model:")
    print(f"  State: {state[:5]}... (showing first 5)")
    print(f"  Valid actions: {np.where(action_mask == 1)[0]}")

    # Get action
    action = model.get_action(state, action_mask=action_mask, deterministic=True)

    action_names = ["Shoot Enemy", "Shoot Self", "Use Magnifier", "Use Cigarette",
                    "Use Beer", "Use Saw", "Use Handcuff", "Use Phone", "Ready"]

    print(f"\n  Model chose: {action} ({action_names[action]})")

    # Get full output (logits only)
    state_tensor = torch.FloatTensor(state).unsqueeze(0)
    with torch.no_grad():
        logits = model(state_tensor)

    print(f"\n  Action logits: {logits.squeeze().numpy()}")

    # Save the pure PyTorch model
    torch.save(model.state_dict(), "torch_model_checkpoint/pytorch_pure.pth")
    print(f"\n✓ Saved pure PyTorch weights to: torch_model_checkpoint/pytorch_pure.pth")

    # Load it back
    model2 = BuckshotActorCritic()
    model2.load_state_dict(torch.load("torch_model_checkpoint/pytorch_pure.pth"))
    model2.eval()
    print(f"✓ Loaded pure PyTorch weights successfully!")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    # Show architecture
    print("=" * 80)
    print("PURE PYTORCH MODEL ARCHITECTURE")
    print("=" * 80)

    model = BuckshotActorCritic()
    print(model)

    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    print(f"\nTotal parameters: {total_params:,}")

    # Compare with SB3
    compare_outputs()

    # Show usage
    example_usage()
