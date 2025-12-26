import numpy as np

# ============================================================
# 全域設定（照你的 MLP）
# ============================================================
IN_DIM    = 33
H1_DIM    = 128
H2_DIM    = 128
OUT_DIM   = 10
FRAC_BITS = 10
WEIGHT_DIR = "fpga_weights_bin"

# ============================================================
# 工具函式
# ============================================================
def float_to_s5_10(x, frac_bits=FRAC_BITS):
    scale = 1 << frac_bits
    scaled = int(x * scale)
    if scaled > 32767: scaled = 32767
    elif scaled < -32768: scaled = -32768
    return np.int16(scaled)

def s5_10_to_float(v, frac_bits=FRAC_BITS):
    return float(np.int16(v)) / float(1 << frac_bits)

def bin16_to_int16(bits: str) -> np.int16:
    bits = bits.strip()
    if not bits: return np.int16(0)
    v = int(bits, 2)
    if v >= (1 << 15): v -= (1 << 16)
    return np.int16(v)

def load_weight_matrix(filename, out_dim, in_dim):
    path = f"{WEIGHT_DIR}/{filename}"
    lines = [line.strip() for line in open(path) if line.strip()]
    vals = np.fromiter((bin16_to_int16(b) for b in lines), dtype=np.int16)
    return vals.reshape((out_dim, in_dim))

def load_bias_vector(filename, out_dim):
    path = f"{WEIGHT_DIR}/{filename}"
    lines = [line.strip() for line in open(path) if line.strip()]
    vals = np.fromiter((bin16_to_int16(b) for b in lines), dtype=np.int16)
    return vals

# ============================================================
# 單層 FC 模擬（bit-true）
# ============================================================
def fc_layer_s5_10(act_in, W, B, has_relu=True, frac_bits=FRAC_BITS):
    IN_DIM, OUT_DIM = W.shape[1], W.shape[0]
    acc = np.left_shift(B.astype(np.int32), frac_bits)
    for i in range(IN_DIM):
        x = np.int32(act_in[i])
        for o in range(OUT_DIM):
            acc[o] = np.int32(acc[o] + np.int32(x * np.int32(W[o, i])))
    shifted = acc >> frac_bits
    out = np.zeros(OUT_DIM, dtype=np.int16)
    for o in range(OUT_DIM):
        s = np.int32(shifted[o])
        if has_relu and s < 0:
            out[o] = np.int16(0)
        else:
            out[o] = np.int16(np.int32(s & 0xFFFF))
    return out

# ============================================================
# MLP 結構（3 層）
# ============================================================
class FixedMLP_S5_10:
    def __init__(self):
        self.W1 = load_weight_matrix("fc1_weight.txt", H1_DIM, IN_DIM)
        self.B1 = load_bias_vector ("fc1_bias.txt",   H1_DIM)
        self.W2 = load_weight_matrix("fc2_weight.txt", H2_DIM, H1_DIM)
        self.B2 = load_bias_vector ("fc2_bias.txt",   H2_DIM)
        self.W3 = load_weight_matrix("fc3_weight.txt", OUT_DIM, H2_DIM)
        self.B3 = load_bias_vector ("fc3_bias.txt",   OUT_DIM)

    def run_from_fixed_input(self, x_fixed):
        act1 = fc_layer_s5_10(x_fixed, self.W1, self.B1, has_relu=True)
        act2 = fc_layer_s5_10(act1,    self.W2, self.B2, has_relu=True)
        act3 = fc_layer_s5_10(act2,    self.W3, self.B3, has_relu=False)
        return act1, act2, act3

# ============================================================
# 主程式：印出 fc1 / fc2 ReLU 結果
# ============================================================
if __name__ == "__main__":
    input_real = np.array([
        1.0, 1.0, 6.0, 0.0, 0.0, 1.0, 0.0, 3.0, 0.0, 0.0,
        1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 3.0, 0.0, 1.0, 1.0,
        0.0, 1.0, 0.0, 0.0, 1.0, 2.0, 3.0, 3.0, 2.0, 3.0,
        2.0, 1.0, 1.0
    ], dtype=np.float32)

    x_fixed = np.array([float_to_s5_10(v) for v in input_real], dtype=np.int16)
    mlp = FixedMLP_S5_10()
    act1, act2, act3 = mlp.run_from_fixed_input(x_fixed)

    def print_layer(name, arr):
        print(f"===== {name} (S5.10 after ReLU) =====")
        for i, v in enumerate(arr[:128]):  # 只印前 16 個方便觀察
            print(f"{name}[{i:3d}] = 0x{int(v)&0xFFFF:04x}  (dec {int(v):6d}, real {s5_10_to_float(v):+.4f})")
        print("... total", len(arr), "neurons\n")

    print_layer("fc1", act1)
    print_layer("fc2", act2)

    print("===== Final Output (fc3) =====")
    for i, v in enumerate(act3):
        print(f"out[{i}] = 0x{int(v)&0xFFFF:04x}  (dec {int(v):6d}, real {s5_10_to_float(v):+.4f})")
