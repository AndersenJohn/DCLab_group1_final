import torch
import numpy as np
from sb3_contrib import MaskablePPO

# ===========================================================
# 1️⃣ 載入模型
# ===========================================================
model_path = "buckshot_final.zip"  # ← 請確認路徑正確
model = MaskablePPO.load(model_path)
policy = model.policy
policy.eval()

print(f"✓ Model loaded from {model_path}")
print(policy)

# ===========================================================
# 2️⃣ 建立輸入向量（與 FPGA 一致）
# ===========================================================
input_real = np.array([
    1.0, 1.0, 6.0, 0.0, 0.0, 1.0, 0.0, 3.0, 0.0, 0.0,
    1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 3.0, 0.0, 1.0, 1.0,
    0.0, 1.0, 0.0, 0.0, 1.0, 2.0, 3.0, 3.0, 2.0, 3.0,
    2.0, 1.0, 1.0
], dtype=np.float32)

obs = torch.tensor(input_real).unsqueeze(0)  # shape = [1, 33]

# ===========================================================
# 3️⃣ 前向推論（取出 policy head logits）
# ===========================================================
with torch.no_grad():
    latent_pi, latent_vf = policy.mlp_extractor(obs)
    logits = policy.action_net(latent_pi)  # shape [1, 10]
    logits_np = logits.squeeze(0).cpu().numpy()

# ===========================================================
# 4️⃣ 印出結果
# ===========================================================
print("\n===== Inference Result (PyTorch, FP32) =====")
for i, val in enumerate(logits_np):
    print(f"out[{i}] = {val:+.6f}")
print("=============================================")

# 若要看 argmax (對應 FPGA 的最終分類)
print(f"\nArgmax index = {np.argmax(logits_np)}")
