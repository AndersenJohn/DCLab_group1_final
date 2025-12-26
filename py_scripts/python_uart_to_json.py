import serial
import time
import json
import os

# --- 設定區 ---
COM_PORT = 'COM4'  # 請確認你的裝置管理員
BAUD_RATE = 115200
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "game_logs")  # JSON 存檔的資料夾名稱

# 狀態名稱對照表 (方便 Debug 用，不影響 JSON 數值)
STATE_MAP = {
    0: "IDLE", 1: "LOAD", 2: "ITEM_P0", 3: "ITEM_P1",
    4: "ITEM_PROC", 5: "SHOOT_P0", 6: "SHOOT_P1", 
    7: "SHOOT_PROC", 8: "DONE",9: "ITEM_INTO_LOAD",10: "SHOOT_INTO_LOAD",
    11: "INTO_ITEM_P0_WAIT",12: "INTO_ITEM_P1_WAIT",13: "SHOOT_INTO_P0_WAIT",14: "SHOOT_INTO_P1_WAIT",
    15: "INTO_DONE"
}

def parse_packet(packet):
    """
    解析 14 Bytes 的封包數據
    packet: bytearray or list of int (length 14)
    """
    # Byte 0 is Header (0xA5), skip it in logic, start from Byte 1
    
    # Byte 1: { Winner(2), State(4), PlayerA(1), PlayerB(1) }
    b1 = packet[1]
    winner = (b1 >> 6) & 0x03
    state_val = (b1 >> 2) & 0x0F
    player_a = (b1 >> 1) & 0x01
    player_b = b1 & 0x01

    # Byte 2: { Saw(1), Rev(1), Handcuff(1), RptValid(1), Report(1), RptIdx(3) }
    b2 = packet[2]
    saw_active = (b2 >> 7) & 0x01
    rev_active = (b2 >> 6) & 0x01
    handcuff_active = (b2 >> 5) & 0x01
    rpt_valid = (b2 >> 4) & 0x01
    rpt_val = (b2 >> 3) & 0x01
    rpt_idx = b2 & 0x07

    # Byte 3: { HP_P0(3), 1'b0, HP_P1(3), 1'b0 }
    b3 = packet[3]
    hp_p0 = (b3 >> 5) & 0x07
    hp_p1 = (b3 >> 1) & 0x07

    # Byte 4: { TotalBullets(4), BulletRemain(4) }
    b4 = packet[4]
    total_bullets = (b4 >> 4) & 0x0F
    bullet_remain = b4 & 0x0F

    # Byte 5: { BulletFilled(3), 1'b0, BulletEmpty(3), 1'b0 }
    b5 = packet[5]
    bullet_filled = (b5 >> 5) & 0x07
    bullet_empty = (b5 >> 1) & 0x07

    # Byte 6: { BulletBitmapPtr(4), 4'b0 }
    b6 = packet[6]
    bitmap_ptr = (b6 >> 4) & 0x0F

    # Byte 7: BulletBitmap(8)
    b7 = packet[7]
    bullet_bitmap = b7

    # Byte 8~10: P0 Items (每 Byte 兩個 4-bit Item)
    # Byte 8
    item_p0_0 = (packet[8] >> 4) & 0x0F
    item_p0_1 = packet[8] & 0x0F
    # Byte 9
    item_p0_2 = (packet[9] >> 4) & 0x0F
    item_p0_3 = packet[9] & 0x0F
    # Byte 10
    item_p0_4 = (packet[10] >> 4) & 0x0F
    item_p0_5 = packet[10] & 0x0F

    # Byte 11~13: P1 Items
    # Byte 11
    item_p1_0 = (packet[11] >> 4) & 0x0F
    item_p1_1 = packet[11] & 0x0F
    # Byte 12
    item_p1_2 = (packet[12] >> 4) & 0x0F
    item_p1_3 = packet[12] & 0x0F
    # Byte 13
    item_p1_4 = (packet[13] >> 4) & 0x0F
    item_p1_5 = packet[13] & 0x0F

    # 構建字典
    data_dict = {
        "game_info": {
            "winner": winner,
            "state_code": state_val,
            "state_name": STATE_MAP.get(state_val, "UNKNOWN"),
            "turn_player_a": bool(player_a),
            "turn_player_b": bool(player_b)
        },
        "active_items": {
            "saw": bool(saw_active),
            "reverse": bool(rev_active),
            "handcuff": bool(handcuff_active)
        },
        "bullet_report": {
            "valid": bool(rpt_valid),
            "is_live": bool(rpt_val), # 1=Live, 0=Blank
            "index": rpt_idx
        },
        "hp": {
            "p0": hp_p0,
            "p1": hp_p1
        },
        "bullets": {
            "total": total_bullets,
            "remain": bullet_remain,
            "filled_count": bullet_filled,
            "empty_count": bullet_empty,
            "bitmap_ptr": bitmap_ptr,
            "bitmap_int": bullet_bitmap,
            "bitmap_bin": f"{bullet_bitmap:08b}" # 方便閱讀二進制
        },
        "items_p0": [item_p0_0, item_p0_1, item_p0_2, item_p0_3, item_p0_4, item_p0_5],
        "items_p1": [item_p1_0, item_p1_1, item_p1_2, item_p1_3, item_p1_4, item_p1_5]
    }
    
    return data_dict

def save_to_json(data, counter):
    """將字典存為 stateX.json"""
    filename = os.path.join(OUTPUT_DIR, f"state{counter}.json")
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"[Saved] {filename} (State: {data['game_info']['state_name']})")

def main():
    # 建立輸出目錄
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created directory: {OUTPUT_DIR}")

    state_counter = 0
    buffer = bytearray()

    try:
        ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=0.1)
        print(f"Listening on {COM_PORT} at {BAUD_RATE}...")
        print(f"Waiting for header 0xA5...")

        while True:
            # 讀取所有可用的 bytes 到 buffer
            if ser.in_waiting > 0:
                chunk = ser.read(ser.in_waiting)
                buffer.extend(chunk)

                # 處理 buffer，尋找完整封包 (14 bytes)
                while len(buffer) >= 14:
                    # 檢查 Header
                    if buffer[0] == 0xA5:
                        # 提取一個完整封包
                        packet = buffer[0:14]
                        
                        # 解析數據
                        parsed_data = parse_packet(packet)
                        
                        # 儲存 JSON
                        save_to_json(parsed_data, state_counter)
                        state_counter += 1
                        
                        # 從 buffer 移除已處理的數據
                        del buffer[0:14]
                    else:
                        # 如果第一個 byte 不是 0xA5，代表錯位，移除第一個 byte 繼續找
                        # print(f"Skipping byte {hex(buffer[0])}, waiting for header...")
                        del buffer[0]
            
            # 短暫休息避免 CPU 滿載
            time.sleep(0.01)

    except serial.SerialException as e:
        print(f"Error: Could not open serial port {COM_PORT}.")
        print(f"Details: {e}")
    except KeyboardInterrupt:
        print("\nExiting...")
        if 'ser' in locals() and ser.is_open:
            ser.close()

if __name__ == "__main__":
    main()