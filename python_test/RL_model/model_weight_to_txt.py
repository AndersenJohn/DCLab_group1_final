"""
Script to convert PyTorch model weights to text files for inspection.
"""
import torch
import numpy as np
import os
import sys

class BuckshotActorModel(torch.nn.Module):
    """
    Pure PyTorch implementation matching SB3's MaskableActorCriticPolicy
    """
    def __init__(self):
        super().__init__()

        # Actor Network (Policy Network) - decides actions
        self.policy_net = torch.nn.Sequential(
            torch.nn.Linear(30, 128),
            torch.nn.ReLU(),
            torch.nn.Linear(128, 128),
            torch.nn.ReLU()
        )

        # Action head - outputs action logits
        self.action_head = torch.nn.Linear(128, 9)

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
    


def weight_print(model, checkpoint_dir = "torch_model_checkpoint/pytroch_pure.pth", output_dir="model_weights_txt/"):
    """
    Save model weights to text files.

    Args:
        model: PyTorch model
        checkpoint_dir: Path to the checkpoint file
        output_dir: Directory to save text files
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for name, param in model.state_dict().items():
        weight_array = param.cpu().numpy()
        file_path = os.path.join(output_dir, f"{name.replace('.', '_')}.txt")
        np.savetxt(file_path, weight_array.flatten(), fmt="%.6f")
        print(f"Saved weights of {name} to {file_path}")

if __name__ == "__main__":
    # Example usage with BuckshotActorCritic model
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

    # Initialize model and load weights
    model = BuckshotActorModel()
    model.load_state_dict(torch.load("torch_model_checkpoint\\pytorch_pure.pth"))
    model.eval()

    # Save weights to text files
    weight_print(model)
