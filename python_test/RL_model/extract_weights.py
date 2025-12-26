"""
Extract MLP weights for FPGA:
- fpga_weights_32  → FP32 (original)
- fpga_weights_16  → FP16 (half precision)
- fpga_weights_bin → Fixed-point S5.10 (binary, 16-bit two’s complement)
- fpga_weights_dec_scaled → Fixed-point S5.10 decimal (value / 2^10)
"""

import numpy as np
import torch
from sb3_contrib import MaskablePPO
import os


# ================================================================
#   HELPER FUNCTIONS: Fixed-point Conversion (S5.10, 16-bit)
# ================================================================
def float_to_fixed(value, int_bits=5, frac_bits=10, total_bits=16):
    """
    Convert float → S5.10 fixed-point (two’s complement, 16-bit)
    - 1 sign bit, 5 integer bits, 10 fractional bits
    """
    scale = 1 << frac_bits
    scaled = int(np.round(value * scale))
    max_val = (1 << (total_bits - 1)) - 1   # +32767
    min_val = -(1 << (total_bits - 1))      # -32768
    scaled = max(min_val, min(max_val, scaled))
    if scaled < 0:
        scaled = (1 << total_bits) + scaled  # two's complement
    return scaled


def convert_to_fixed_binary(weights, int_bits=5, frac_bits=10, total_bits=16):
    """
    Convert numpy arrays of weights into S5.10 16-bit binary strings
    """
    fixed_weights = {}
    for name, w in weights.items():
        vals = [format(float_to_fixed(v, int_bits, frac_bits, total_bits), f"0{total_bits}b") for v in w.flatten()]
        fixed_weights[name] = np.array(vals)
    return fixed_weights


def convert_to_fixed_decimal_scaled(weights, frac_bits=10):
    """
    Convert numpy arrays to S5.10 decimal scaled (value / 2^10)
    """
    scale = 1 << frac_bits
    scaled_weights = {}
    for name, w in weights.items():
        vals = np.array([np.round(v * scale) / scale for v in w.flatten()], dtype=np.float64)
        scaled_weights[name] = vals
    return scaled_weights


# ================================================================
#   HELPER FUNCTION: save weights
# ================================================================
def save_dict_txt(weights, output_dir, fmt="%s"):
    os.makedirs(output_dir, exist_ok=True)
    for name, arr in weights.items():
        path = os.path.join(output_dir, f"{name}.txt")
        np.savetxt(path, arr, fmt=fmt)
        print(f"✓ Saved: {path}")


def save_architecture(output_dir, total_params, note=""):
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "architecture.txt")
    with open(path, "w") as f:
        f.write("MLP Architecture for FPGA Implementation\n")
        f.write("=" * 70 + "\n\n")
        f.write("Network Structure:\n")
        f.write("  Input:    33 features\n")
        f.write("  Hidden1:  128 neurons (ReLU)\n")
        f.write("  Hidden2:  128 neurons (ReLU)\n")
        f.write("  Output:   10 logits\n\n")
        f.write(f"Total Parameters: {total_params:,}\n")
        if note:
            f.write(f"\n{note}\n")
    print(f"✓ Saved: {path}")


# ================================================================
#   MAIN FUNCTION
# ================================================================
def extract_mlp_weights(model_path):
    print("=" * 70)
    print("Extracting MLP Weights (FP32, FP16, and S5.10 fixed-point)")
    print("=" * 70)

    print(f"\nLoading model from: {model_path}")
    model = MaskablePPO.load(model_path)
    policy = model.policy

    # ------------------------------------------------------------
    # 1️⃣ Extract FP32
    # ------------------------------------------------------------
    print("\nExtracting FP32 weights...")
    weights_32 = {
        "fc1_weight": policy.mlp_extractor.policy_net[0].weight.detach().cpu().numpy(),
        "fc1_bias":   policy.mlp_extractor.policy_net[0].bias.detach().cpu().numpy(),
        "fc2_weight": policy.mlp_extractor.policy_net[2].weight.detach().cpu().numpy(),
        "fc2_bias":   policy.mlp_extractor.policy_net[2].bias.detach().cpu().numpy(),
        "fc3_weight": policy.action_net.weight.detach().cpu().numpy(),
        "fc3_bias":   policy.action_net.bias.detach().cpu().numpy(),
    }

    total_params = sum(w.size for w in weights_32.values())
    print(f"Total parameters: {total_params:,}")

    # ------------------------------------------------------------
    # 2️⃣ Save FP32 / FP16
    # ------------------------------------------------------------
    print("\nSaving FP32 / FP16 ...")
    save_dict_txt(weights_32, "fpga_weights_32", fmt="%.6f")
    weights_16 = {k: v.astype(np.float16) for k, v in weights_32.items()}
    save_dict_txt(weights_16, "fpga_weights_16", fmt="%.6f")
    save_architecture("fpga_weights_32", total_params, note="Precision: FP32")
    save_architecture("fpga_weights_16", total_params, note="Precision: FP16")

    # ------------------------------------------------------------
    # 3️⃣ Convert to S5.10 fixed-point binary
    # ------------------------------------------------------------
    print("\nConverting to S5.10 fixed-point (binary, 16-bit)...")
    weights_bin = convert_to_fixed_binary(weights_32, int_bits=5, frac_bits=10, total_bits=16)
    save_dict_txt(weights_bin, "fpga_weights_bin", fmt="%s")
    save_architecture("fpga_weights_bin", total_params,
                      note="Format: S5.10 two's complement (binary, 16-bit)")

    # ------------------------------------------------------------
    # 4️⃣ Convert to S5.10 decimal scaled (float)
    # ------------------------------------------------------------
    print("\nCreating scaled decimal version (value / 2^10)...")
    weights_dec_scaled = convert_to_fixed_decimal_scaled(weights_32, frac_bits=10)
    save_dict_txt(weights_dec_scaled, "fpga_weights_dec_scaled", fmt="%.6f")
    save_architecture("fpga_weights_dec_scaled", total_params,
                      note="S5.10 decimal scaled version (value / 2^10)")

    # ------------------------------------------------------------
    # ✅ Done
    # ------------------------------------------------------------
    print("\n==============================================================")
    print("✔ Extraction Complete")
    print("📁 Saved FP32 → fpga_weights_32/")
    print("📁 Saved FP16 → fpga_weights_16/")
    print("📁 Saved S5.10 (binary)  → fpga_weights_bin/")
    print("📁 Saved S5.10 (decimal /2^10) → fpga_weights_dec_scaled/")
    print("==============================================================")

    return weights_32, weights_16, weights_bin, weights_dec_scaled


# ================================================================
#   Script Entry
# ================================================================
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Extract MLP weights for FPGA (FP32, FP16, S5.10 fixed)")
    parser.add_argument("model", type=str,
                        help="Path to model (e.g., models/buckshot_final)")
    args = parser.parse_args()
    extract_mlp_weights(args.model)
