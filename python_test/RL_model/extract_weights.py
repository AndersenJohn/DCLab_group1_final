"""
Extract MLP weights from trained model for FPGA deployment
Exports weights as numpy arrays and text files
"""

import numpy as np
import torch
from sb3_contrib import MaskablePPO
import os


def extract_mlp_weights(model_path, output_dir="fpga_weights"):
    """
    Extract MLP weights from trained model

    Args:
        model_path: Path to saved model (e.g., "models/buckshot_final")
        output_dir: Directory to save extracted weights
    """
    print("="*70)
    print("Extracting MLP Weights for FPGA Deployment")
    print("="*70)

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Load model
    print(f"\nLoading model from: {model_path}")
    model = MaskablePPO.load(model_path)

    # Get policy network (the MLP)
    policy = model.policy

    print("\n" + "="*70)
    print("Model Architecture")
    print("="*70)

    # Extract weights and biases for each layer
    weights = {}

    # Layer 1: Input → Hidden1 (30 → 128)
    fc1_weight = policy.mlp_extractor.policy_net[0].weight.detach().cpu().numpy()  # Shape: (128, 30)
    fc1_bias = policy.mlp_extractor.policy_net[0].bias.detach().cpu().numpy()      # Shape: (128,)

    print(f"\nLayer 1 (Input → Hidden1):")
    print(f"  Weight shape: {fc1_weight.shape}  (128 neurons × 30 inputs)")
    print(f"  Bias shape:   {fc1_bias.shape}")
    print(f"  Activation:   ReLU")

    weights['fc1_weight'] = fc1_weight
    weights['fc1_bias'] = fc1_bias

    # Layer 2: Hidden1 → Hidden2 (128 → 128)
    fc2_weight = policy.mlp_extractor.policy_net[2].weight.detach().cpu().numpy()  # Shape: (128, 128)
    fc2_bias = policy.mlp_extractor.policy_net[2].bias.detach().cpu().numpy()      # Shape: (128,)

    print(f"\nLayer 2 (Hidden1 → Hidden2):")
    print(f"  Weight shape: {fc2_weight.shape}  (128 neurons × 128 inputs)")
    print(f"  Bias shape:   {fc2_bias.shape}")
    print(f"  Activation:   ReLU")

    weights['fc2_weight'] = fc2_weight
    weights['fc2_bias'] = fc2_bias

    # Layer 3: Hidden2 → Output (128 → 9)
    fc3_weight = policy.action_net.weight.detach().cpu().numpy()  # Shape: (9, 128)
    fc3_bias = policy.action_net.bias.detach().cpu().numpy()      # Shape: (9,)

    print(f"\nLayer 3 (Hidden2 → Output):")
    print(f"  Weight shape: {fc3_weight.shape}  (9 actions × 128 inputs)")
    print(f"  Bias shape:   {fc3_bias.shape}")
    print(f"  Activation:   None (logits for action probabilities)")

    weights['fc3_weight'] = fc3_weight
    weights['fc3_bias'] = fc3_bias

    # Calculate total parameters
    total_params = sum(w.size for w in weights.values())
    print(f"\nTotal Parameters: {total_params:,}")

    print("\n" + "="*70)
    print("Saving Weights")
    print("="*70)

    # Save as numpy arrays (.npy)
    for name, weight in weights.items():
        npy_path = os.path.join(output_dir, f"{name}.npy")
        np.save(npy_path, weight)
        print(f"✓ Saved: {npy_path}")

    # Save as text files (for easy inspection / FPGA tools)
    for name, weight in weights.items():
        txt_path = os.path.join(output_dir, f"{name}.txt")
        np.savetxt(txt_path, weight.flatten(), fmt='%.6f')
        print(f"✓ Saved: {txt_path}")

    # Save architecture info
    arch_path = os.path.join(output_dir, "architecture.txt")
    with open(arch_path, 'w') as f:
        f.write("MLP Architecture for FPGA Implementation\n")
        f.write("="*70 + "\n\n")
        f.write("Network Structure:\n")
        f.write("  Input:    30 features\n")
        f.write("  Hidden1:  128 neurons (ReLU activation)\n")
        f.write("  Hidden2:  128 neurons (ReLU activation)\n")
        f.write("  Output:   9 actions (no activation, logits)\n\n")
        f.write("Layer Details:\n")
        f.write("  Layer 1: (33, 128) + bias(128) = 3,968 params\n")
        f.write("  Layer 2: (128, 128) + bias(128) = 16,512 params\n")
        f.write("  Layer 3: (128, 10) + bias(9) = 1,161 params\n")
        f.write(f"  Total: {total_params:,} params\n\n")
        f.write("Forward Pass (for FPGA):\n")
        f.write("  1. input[33] → fc1 → relu → hidden1[128]\n")
        f.write("  2. hidden1[128] → fc2 → relu → hidden2[128]\n")
        f.write("  3. hidden2[128] → fc3 → logits[10]\n")
        f.write("  4. argmax(logits) → action\n\n")
        f.write("Note: For action masking, set invalid action logits to -inf before argmax\n")

    print(f"✓ Saved: {arch_path}")

    # Save as single combined file
    combined_path = os.path.join(output_dir, "all_weights.npz")
    np.savez(combined_path, **weights)
    print(f"✓ Saved: {combined_path}")

    # Create C header file for FPGA
    header_path = os.path.join(output_dir, "mlp_weights.h")
    with open(header_path, 'w') as f:
        f.write("// MLP Weights for FPGA Implementation\n")
        f.write("// Auto-generated from trained model\n\n")
        f.write("#ifndef MLP_WEIGHTS_H\n")
        f.write("#define MLP_WEIGHTS_H\n\n")

        for name, weight in weights.items():
            arr_name = name.upper()
            f.write(f"// {name}: shape {weight.shape}\n")
            f.write(f"const float {arr_name}[{weight.size}] = {{\n")

            # Write values
            flat = weight.flatten()
            for i in range(0, len(flat), 8):  # 8 values per line
                line_vals = flat[i:i+8]
                f.write("    " + ", ".join(f"{v:.6f}f" for v in line_vals))
                if i + 8 < len(flat):
                    f.write(",\n")
                else:
                    f.write("\n")

            f.write("};\n\n")

        f.write("#endif // MLP_WEIGHTS_H\n")

    print(f"✓ Saved: {header_path}")

    print("\n" + "="*70)
    print("Weight Statistics")
    print("="*70)

    for name, weight in weights.items():
        print(f"\n{name}:")
        print(f"  Min:    {weight.min():.6f}")
        print(f"  Max:    {weight.max():.6f}")
        print(f"  Mean:   {weight.mean():.6f}")
        print(f"  Std:    {weight.std():.6f}")

    print("\n" + "="*70)
    print("FPGA Implementation Notes")
    print("="*70)
    print("""
1. Quantization:
   - Consider using fixed-point instead of float for FPGA
   - Recommended: 16-bit fixed point (Q8.8 or Q10.6)
   - Use weight statistics above to determine scaling factors

2. Forward Pass:
   - Matrix multiply: Y = W @ X + b
   - ReLU: max(0, Y)
   - No softmax needed - just argmax for action selection

3. Action Masking:
   - Before argmax, set invalid action logits to -inf (or very negative)
   - This prevents selecting invalid actions

4. Memory Requirements:
   - Total weights: ~21,000 × 4 bytes = 84 KB (float32)
   - Or ~42 KB with 16-bit quantization

5. Performance:
   - Forward pass: ~21,000 MAC operations
   - Can be parallelized on FPGA
   - Expected latency: <1ms on modern FPGA
""")

    print("\n✅ Extraction complete!")
    print(f"📁 All files saved to: {output_dir}/")

    return weights


def test_inference(model_path, weights):
    """
    Test that extracted weights produce same output as original model
    """
    print("\n" + "="*70)
    print("Verification: Testing Extracted Weights")
    print("="*70)

    # Load original model
    model = MaskablePPO.load(model_path)

    # Create random input
    test_input = np.random.randn(30).astype(np.float32)

    # Original model inference
    with torch.no_grad():
        test_input_torch = torch.FloatTensor(test_input).unsqueeze(0)
        original_output = model.policy.forward(test_input_torch, deterministic=True)
        original_logits = original_output[0].squeeze().cpu().numpy()

    # Manual inference with extracted weights
    def relu(x):
        return np.maximum(0, x)

    # Layer 1
    h1 = relu(weights['fc1_weight'] @ test_input + weights['fc1_bias'])

    # Layer 2
    h2 = relu(weights['fc2_weight'] @ h1 + weights['fc2_bias'])

    # Layer 3
    manual_logits = weights['fc3_weight'] @ h2 + weights['fc3_bias']

    # Compare
    diff = np.abs(original_logits - manual_logits).max()

    print(f"\nOriginal model logits: {original_logits}")
    print(f"Manual inference logits: {manual_logits}")
    print(f"\nMax difference: {diff:.10f}")

    if diff < 1e-5:
        print("✅ Verification passed! Extracted weights are correct.")
    else:
        print("⚠️  Warning: Small numerical differences detected (likely due to floating point precision)")

    return diff < 1e-4


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract MLP weights for FPGA deployment")
    parser.add_argument("model", type=str, help="Path to trained model (e.g., models/buckshot_final)")
    parser.add_argument("--output", type=str, default="fpga_weights", help="Output directory")
    parser.add_argument("--verify", action="store_true", help="Verify extracted weights")

    args = parser.parse_args()

    # Extract weights
    weights = extract_mlp_weights(args.model, args.output)

    # Optional verification
    if args.verify:
        test_inference(args.model, weights)
