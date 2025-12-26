import os
import time

# ===== 路徑設定（同一層）=====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_FILE = os.path.join(BASE_DIR, "Commands.txt")
DST_DIR  = os.path.join(BASE_DIR, "Commands")

# ===== 參數設定 =====
INTERVAL_SEC = 10   # 每 10 秒
BATCH_SIZE   = 1    # 每次寫4行

# ===== 檢查來源檔 =====
if not os.path.isfile(SRC_FILE):
    raise FileNotFoundError("找不到 Commands.txt")

# ===== 建立目標資料夾 =====
os.makedirs(DST_DIR, exist_ok=True)

# ===== 讀取 Commands.txt =====
with open(SRC_FILE, "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f if line.strip()]

total = len(lines)
index = 0
file_id = 0

# ===== 逐批寫出 =====
while index < total:

    for _ in range(BATCH_SIZE):
        if index >= total:
            break

        cmd = lines[index]
        filename = f"{file_id:03d}.txt"
        path = os.path.join(DST_DIR, filename)

        with open(path, "w", encoding="utf-8") as out:
            out.write(cmd + "\n")

        print(f"  {filename} -> {cmd}")

        index += 1
        file_id += 1

    if index < total:
        time.sleep(INTERVAL_SEC)


