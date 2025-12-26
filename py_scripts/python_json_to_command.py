import json
import os
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_FILE = os.path.join(BASE_DIR, "python_code", "game_logs")
DST_DIR  = os.path.join(BASE_DIR, "Commands")

# Default state
# Items Numbering:
# Magnifier: 8      M
# Cigarette: 9      C
# Handcuff: 10      H
# Saw: 11           S
# Beer: 12          B
# Phone: 13         P
# Reverse: 14       R
default_state = {
    "game_info": {
        "winner": 0,
        "state_code": 0,
        "state_name": "ITEM_INTO_LOAD",
        "turn_player_a": False,
        "turn_player_b": False
    },
    "active_items": {
        "saw": False,
        "reverse": False,
        "handcuff": False
    },
    "bullet_report": {
        "valid": False,
        "is_live": False,
        "index": 0
    },
    "hp": {
        "p0": 0,
        "p1": 0
    },
    "bullets": {
        "total": 0,
        "remain": 0,
        "filled_count": 0,
        "empty_count": 0,
        "bitmap_ptr": 0,
        "bitmap_int": 0,
        "bitmap_bin": "00000000"
    },
    "items_p0": [
        0,
        0,
        0,
        0,
        0,
        0
    ],
    "items_p1": [
        0,
        0,
        0,
        0,
        0,
        0,
        0
    ]
}

# items value mapping
item_map = {
    0: "",
    8: "M",
    9: "C",
    10: "H",
    11: "S",
    12: "B",
    13: "P",
    14: "R",
} 
item_p0_position_map = {
    0: "1",
    1: "2",
    2: "3",
    3: "4",
    4: "5",
    5: "6"
}
item_p1_position_map = {
    0: "7",
    1: "8",
    2: "9",
    3: "0",
    4: "-",
    5: "="
}

def get_changes(old_state, new_state):
    changes = {}
    for key in new_state:
        if key not in old_state or old_state[key] != new_state[key]:
            changes[key] = new_state[key]
    return changes

def get_future_state(next_state_num):
    path = os.path.join(SRC_FILE, f"state{next_state_num}.json")
    while not os.path.exists(path):
        time.sleep(0.05)
    
    while True:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            time.sleep(0.05)
            continue

def write_command_file(filename, content):
    filepath = os.path.join(DST_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())

def get_p0_use_item_command(old_state, new_state, item_pos_index):
    command = ""
    if item_map[old_state["items_p0"][item_pos_index]] == "M":
        if new_state["bullet_report"]["is_live"]:
            command = "ML"
        else:
            command = "MB"
    elif item_map[old_state["items_p0"][item_pos_index]] == "C":
        command = "C"
    elif item_map[old_state["items_p0"][item_pos_index]] == "H":
        command = "H"
    elif item_map[old_state["items_p0"][item_pos_index]] == "S":
        command = "S"
    elif item_map[old_state["items_p0"][item_pos_index]] == "B":
        if new_state["bullets"]["filled_count"] != old_state["bullets"]["filled_count"]:
            command = "BL"
        else:
            command = "BB"
    elif item_map[old_state["items_p0"][item_pos_index]] == "P":
        index = new_state["bullet_report"]["index"]
        live = "L" if new_state["bullet_report"]["is_live"] else "B"
        command = f"P{index}{live}"
    elif item_map[old_state["items_p0"][item_pos_index]] == "R":
        command = "R"
    command = item_p0_position_map[item_pos_index] + command
    return command

def get_p1_use_item_command(old_state, new_state, item_pos_index):
    command = ""
    if item_map[old_state["items_p1"][item_pos_index]] == "M":
        if new_state["bullet_report"]["is_live"]:
            command = "ML"
        else:
            command = "MB"
    elif item_map[old_state["items_p1"][item_pos_index]] == "C":
        command = "C"
    elif item_map[old_state["items_p1"][item_pos_index]] == "H":
        command = "H"
    elif item_map[old_state["items_p1"][item_pos_index]] == "S":
        command = "S"
    elif item_map[old_state["items_p1"][item_pos_index]] == "B":
        if new_state["bullets"]["filled_count"] != old_state["bullets"]["filled_count"]:
            command = "BL"
        else:
            command = "BB"
    elif item_map[old_state["items_p1"][item_pos_index]] == "P":
        index = new_state["bullet_report"]["index"]
        live = "L" if new_state["bullet_report"]["is_live"] else "B"
        command = f"P{index}{live}"
    elif item_map[old_state["items_p1"][item_pos_index]] == "R":
        command = "R"
    command = item_p1_position_map[item_pos_index] + command
    return command

def get_p0_bullet_change_command(old_state, new_state, future_state=None):
    # Q: Blue->Blue Damage = 1
    # W: Blue->Blue Damage = 2
    # E: Blue->Red Damage = 1
    # R: Blue->Red Damage = 2
    command = ""
    if old_state["bullets"]["filled_count"] != new_state["bullets"]["filled_count"]:
        bullet_command = "L"
    else:
        bullet_command = "B"

    if old_state["active_items"]["reverse"] == True:
        bullet_command = "B" if bullet_command == "L" else "L"

    # Determine Target
    target = "self"
    if new_state["hp"]["p1"] < old_state["hp"]["p1"]:
        target = "opponent"
    elif new_state["hp"]["p0"] < old_state["hp"]["p0"]:
        target = "self"
    elif "P1" in new_state["game_info"]["state_name"]:
        target = "opponent"
    elif "P0" in new_state["game_info"]["state_name"]:
        target = "self"
    elif future_state:
        if "P1" in future_state["game_info"]["state_name"]:
            target = "opponent"
        elif "P0" in future_state["game_info"]["state_name"]:
            target = "self"
        elif old_state["game_info"]["turn_player_a"] != future_state["game_info"]["turn_player_a"]:
            target = "opponent"
        else:
            target = "self"
    else:
        if old_state["active_items"]["handcuff"]:
            if not new_state["active_items"]["handcuff"]:
                target = "opponent"
            else:
                target = "self"
        else:
            if old_state["game_info"]["turn_player_a"] != new_state["game_info"]["turn_player_a"]:
                target = "opponent"
            else:
                target = "self"

    is_saw = old_state["active_items"]["saw"]
    if target == "opponent":
        shoot_command = "R" if is_saw else "E"
    else:
        shoot_command = "W" if is_saw else "Q"
    
    command = shoot_command + bullet_command
    return command

def get_p1_bullet_change_command(old_state, new_state, future_state=None):
    # T: Red->Blue Damage = 1
    # Y: Red->Blue Damage = 2
    # U: Red->Red Damage = 1
    # I: Red->Red Damage = 2
    command = ""
    if old_state["bullets"]["filled_count"] != new_state["bullets"]["filled_count"]:
        bullet_command = "L"
    else:
        bullet_command = "B"

    if old_state["active_items"]["reverse"] == True:
        bullet_command = "B" if bullet_command == "L" else "L"
    
    target = "self"
    
    if new_state["hp"]["p0"] < old_state["hp"]["p0"]:
        target = "opponent"
    elif new_state["hp"]["p1"] < old_state["hp"]["p1"]:
        target = "self"
    elif "P0" in new_state["game_info"]["state_name"]:
        target = "opponent"
    elif "P1" in new_state["game_info"]["state_name"]:
        target = "self"
    elif future_state:
        if "P0" in future_state["game_info"]["state_name"]:
            target = "opponent"
        elif "P1" in future_state["game_info"]["state_name"]:
            target = "self"
        elif old_state["game_info"]["turn_player_b"] != future_state["game_info"]["turn_player_b"]:
            target = "opponent"
        else:
            target = "self"
    else:
        if old_state["active_items"]["handcuff"]:
            if not new_state["active_items"]["handcuff"]:
                target = "opponent"
            else:
                target = "self"
        else:
            if old_state["game_info"]["turn_player_a"] == new_state["game_info"]["turn_player_a"]:
                target = "opponent"
            else:
                target = "self"

    is_saw = old_state["active_items"]["saw"]
    if target == "opponent":
        shoot_command = "Y" if is_saw else "T"
    else:
        shoot_command = "I" if is_saw else "U"

    command = shoot_command + bullet_command
    return command

def get_hp_command(old_state, new_state):
    command = f"({new_state['hp']['p1']},{new_state['hp']['p0']})"
    return command

def get_bullet_count_command(old_state, new_state):
    command = f"{{{new_state['bullets']['filled_count']},{new_state['bullets']['empty_count']}}}"
    return command

game_state_num = 0
command_num = 0
old_state = default_state
new_state = default_state
while True:
    json_path = os.path.join(SRC_FILE, f"state{game_state_num}.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                new_state = json.load(f)
        except json.JSONDecodeError:
            time.sleep(0.05)
            continue
        changes = get_changes(old_state, new_state)

        # INTO_DONE CHECK
        if new_state["game_info"]["state_name"] == "INTO_DONE":
            if old_state["game_info"]["state_name"] == "INTO_ITEM_P0_WAIT":
                command = get_p0_bullet_change_command(old_state, new_state)
                write_command_file(f"{command_num:03d}.txt", command)
                command_num += 1
                command = get_hp_command(old_state, new_state)
                write_command_file(f"{command_num:03d}.txt", command)
                command_num += 1
            elif old_state["game_info"]["state_name"] == "INTO_ITEM_P1_WAIT":
                command = get_p1_bullet_change_command(old_state, new_state)
                write_command_file(f"{command_num:03d}.txt", command)
                command_num += 1
                command = get_hp_command(old_state, new_state)
                write_command_file(f"{command_num:03d}.txt", command)
                command_num += 1
            elif old_state["game_info"]["state_name"] == "SHOOT_INTO_P0_WAIT":
                command = get_p0_bullet_change_command(old_state, new_state)
                write_command_file(f"{command_num:03d}.txt", command)
                command_num += 1
                command = get_hp_command(old_state, new_state)
                write_command_file(f"{command_num:03d}.txt", command)
                command_num += 1
            elif old_state["game_info"]["state_name"] == "SHOOT_INTO_P1_WAIT":
                command = get_p1_bullet_change_command(old_state, new_state)
                write_command_file(f"{command_num:03d}.txt", command)
                command_num += 1
                command = get_hp_command(old_state, new_state)
                write_command_file(f"{command_num:03d}.txt", command)
                command_num += 1
        
        # SHOOT_INTO_LOAD CHECK
        elif old_state["game_info"]["state_name"] == "SHOOT_INTO_LOAD":
            # If new_state state_name is also INTO_LOAD, do nothing
            if new_state["game_info"]["state_name"] == "SHOOT_INTO_LOAD":
                pass
            elif new_state["game_info"]["state_name"] == "ITEM_INTO_LOAD":
                pass
            else:
                # Generate LOAD command
                # 1. add items
                b_cmds = "".join([f"[B{i}:{item_map.get(x, '')}]" for i, x in enumerate(new_state["items_p0"][:6])])
                r_cmds = "".join([f"[R{i}:{item_map.get(x, '')}]" for i, x in enumerate(new_state["items_p1"][:6])])
                write_command_file(f"{command_num:03d}.txt", b_cmds + r_cmds)
                command_num += 1
                # 2. add bullets
                # filled at first, then empty
                command = get_bullet_count_command(old_state, new_state)
                write_command_file(f"{command_num:03d}.txt", command)
                command_num += 1
                # Update HP
                command = get_hp_command(old_state, new_state)
                write_command_file(f"{command_num:03d}.txt", command)
                command_num += 1

        # ITEM_INTO_LOAD CHECK
        elif old_state["game_info"]["state_name"] == "ITEM_INTO_LOAD":
            # If new_state state_name is also INTO_LOAD, do nothing
            if new_state["game_info"]["state_name"] == "SHOOT_INTO_LOAD":
                pass
            elif new_state["game_info"]["state_name"] == "ITEM_INTO_LOAD":
                pass
            else:
                # Generate LOAD command
                # 1. add items
                with open(os.path.join(DST_DIR, f"{command_num:03d}.txt"), "w", encoding="utf-8") as f:        
                    b_cmds = "".join([f"[B{i}:{item_map.get(x, '')}]" for i, x in enumerate(new_state["items_p0"][:6])])
                    r_cmds = "".join([f"[R{i}:{item_map.get(x, '')}]" for i, x in enumerate(new_state["items_p1"][:6])])
                    f.write(b_cmds + r_cmds)
                command_num += 1
                # 2. add bullets
                # filled at first, then empty
                with open(os.path.join(DST_DIR, f"{command_num:03d}.txt"), "w", encoding="utf-8") as f:
                    f.write(f"{{{new_state['bullets']['filled_count']},{new_state['bullets']['empty_count']}}}")
                command_num += 1
                # 3. Update HP
                command = get_hp_command(old_state, new_state)
                with open(os.path.join(DST_DIR, f"{command_num:03d}.txt"), "w", encoding="utf-8") as f:
                    f.write(command)
                command_num += 1

        # INTO_ITEM_P0_WAIT CHECK
        elif old_state["game_info"]["state_name"] == "INTO_ITEM_P0_WAIT":
            if new_state["game_info"]["state_name"] == "INTO_ITEM_P0_WAIT":
                if "items_p0" in changes:
                    for i in range(6):
                        if old_state["items_p0"][i] != new_state["items_p0"][i]:
                            command = get_p0_use_item_command(old_state, new_state, i)
                            with open(os.path.join(DST_DIR, f"{command_num:03d}.txt"), "w", encoding="utf-8") as f:
                                f.write(command)
                            command_num += 1
                    command = get_hp_command(old_state, new_state)
                    with open(os.path.join(DST_DIR, f"{command_num:03d}.txt"), "w", encoding="utf-8") as f:
                        f.write(command)
                    command_num += 1

            elif new_state["game_info"]["state_name"] == "INTO_ITEM_P1_WAIT":
                pass

            elif new_state["game_info"]["state_name"] == "SHOOT_INTO_P0_WAIT":
                command = get_p0_bullet_change_command(old_state, new_state)
                with open(os.path.join(DST_DIR, f"{command_num:03d}.txt"), "w", encoding="utf-8") as f:
                    f.write(command)
                command_num += 1
                command = get_hp_command(old_state, new_state)
                with open(os.path.join(DST_DIR, f"{command_num:03d}.txt"), "w", encoding="utf-8") as f:
                    f.write(command)
                command_num += 1

            elif new_state["game_info"]["state_name"] == "SHOOT_INTO_P1_WAIT":
                command = get_p0_bullet_change_command(old_state, new_state)
                with open(os.path.join(DST_DIR, f"{command_num:03d}.txt"), "w", encoding="utf-8") as f:
                    f.write(command)
                command_num += 1
                command = get_hp_command(old_state, new_state)
                with open(os.path.join(DST_DIR, f"{command_num:03d}.txt"), "w", encoding="utf-8") as f:
                    f.write(command)
                command_num += 1

            elif new_state["game_info"]["state_name"] == "SHOOT_INTO_LOAD":
                future_state = get_future_state(game_state_num + 1)
                command = get_p0_bullet_change_command(old_state, new_state, future_state)
                with open(os.path.join(DST_DIR, f"{command_num:03d}.txt"), "w", encoding="utf-8") as f:
                    f.write(command)
                command_num += 1
                command = get_hp_command(old_state, new_state)
                with open(os.path.join(DST_DIR, f"{command_num:03d}.txt"), "w", encoding="utf-8") as f:
                    f.write(command)
                command_num += 1

            elif new_state["game_info"]["state_name"] == "ITEM_INTO_LOAD":
                if "items_p0" in changes:
                    for i in range(6):
                        if old_state["items_p0"][i] != new_state["items_p0"][i]:
                            command = get_p0_use_item_command(old_state, new_state, i)
                            with open(os.path.join(DST_DIR, f"{command_num:03d}.txt"), "w", encoding="utf-8") as f:
                                f.write(command)
                            command_num +=1

        # INTO_ITEM_P1_WAIT CHECK
        elif old_state["game_info"]["state_name"] == "INTO_ITEM_P1_WAIT":
            if new_state["game_info"]["state_name"] == "INTO_ITEM_P0_WAIT":
                pass

            elif new_state["game_info"]["state_name"] == "INTO_ITEM_P1_WAIT":
                if "items_p1" in changes:
                    for i in range(6):
                        if old_state["items_p1"][i] != new_state["items_p1"][i]:
                            command = get_p1_use_item_command(old_state, new_state, i)
                            write_command_file(f"{command_num:03d}.txt", command)
                            command_num += 1
                    command = get_hp_command(old_state, new_state)
                    write_command_file(f"{command_num:03d}.txt", command)
                    command_num += 1

            elif new_state["game_info"]["state_name"] == "SHOOT_INTO_P1_WAIT":
                command = get_p1_bullet_change_command(old_state, new_state)
                write_command_file(f"{command_num:03d}.txt", command)
                command_num += 1
                command = get_hp_command(old_state, new_state)
                write_command_file(f"{command_num:03d}.txt", command)
                command_num += 1

            elif new_state["game_info"]["state_name"] == "SHOOT_INTO_P0_WAIT":
                command = get_p1_bullet_change_command(old_state, new_state)
                write_command_file(f"{command_num:03d}.txt", command)
                command_num += 1
                command = get_hp_command(old_state, new_state)
                write_command_file(f"{command_num:03d}.txt", command)
                command_num += 1

            elif new_state["game_info"]["state_name"] == "SHOOT_INTO_LOAD":
                future_state = get_future_state(game_state_num + 1)
                command = get_p1_bullet_change_command(old_state, new_state, future_state)
                write_command_file(f"{command_num:03d}.txt", command)
                command_num += 1
                command = get_hp_command(old_state, new_state)
                write_command_file(f"{command_num:03d}.txt", command)
                command_num += 1

            elif new_state["game_info"]["state_name"] == "ITEM_INTO_LOAD":
                if "items_p1" in changes:
                    for i in range(6):
                        if old_state["items_p1"][i] != new_state["items_p1"][i]:
                            command = get_p1_use_item_command(old_state, new_state, i)
                            write_command_file(f"{command_num:03d}.txt", command)
                            command_num += 1

        # SHOOT_INTO_P0_WAIT CHECK
        elif old_state["game_info"]["state_name"] == "SHOOT_INTO_P0_WAIT":
            if new_state["game_info"]["state_name"] == "INTO_ITEM_P0_WAIT":
                if "items_p0" in changes:
                    for i in range(6):
                        if old_state["items_p0"][i] != new_state["items_p0"][i]:
                            command = get_p0_use_item_command(old_state, new_state, i)
                            write_command_file(f"{command_num:03d}.txt", command)
                            command_num += 1
                    command = get_hp_command(old_state, new_state)
                    write_command_file(f"{command_num:03d}.txt", command)
                    command_num += 1

            elif new_state["game_info"]["state_name"] == "INTO_ITEM_P1_WAIT":
                if "items_p1" in changes:
                    for i in range(6):
                        if old_state["items_p1"][i] != new_state["items_p1"][i]:
                            command = get_p1_use_item_command(old_state, new_state, i)
                            write_command_file(f"{command_num:03d}.txt", command)
                            command_num += 1
                    command = get_hp_command(old_state, new_state)
                    write_command_file(f"{command_num:03d}.txt", command)
                    command_num += 1

            elif new_state["game_info"]["state_name"] == "SHOOT_INTO_P0_WAIT":
                pass

            elif new_state["game_info"]["state_name"] == "SHOOT_INTO_P1_WAIT":
                command = get_p0_bullet_change_command(old_state, new_state)
                write_command_file(f"{command_num:03d}.txt", command)
                command_num += 1
                command = get_hp_command(old_state, new_state)
                write_command_file(f"{command_num:03d}.txt", command)
                command_num += 1

            elif new_state["game_info"]["state_name"] == "SHOOT_INTO_LOAD":
                future_state = get_future_state(game_state_num + 1)
                command = get_p0_bullet_change_command(old_state, new_state, future_state)
                write_command_file(f"{command_num:03d}.txt", command)
                command_num += 1
                command = get_hp_command(old_state, new_state)
                write_command_file(f"{command_num:03d}.txt", command)
                command_num += 1

            elif new_state["game_info"]["state_name"] == "ITEM_INTO_LOAD":
                if "items_p0" in changes:
                    for i in range(6):
                        if old_state["items_p0"][i] != new_state["items_p0"][i]:
                            command = get_p0_use_item_command(old_state, new_state, i)
                            write_command_file(f"{command_num:03d}.txt", command)
                            command_num += 1

        # SHOOT_INTO_P1_WAIT CHECK
        elif old_state["game_info"]["state_name"] == "SHOOT_INTO_P1_WAIT":
            if new_state["game_info"]["state_name"] == "INTO_ITEM_P0_WAIT":
                if "items_p0" in changes:
                    for i in range(6):
                        if old_state["items_p0"][i] != new_state["items_p0"][i]:
                            command = get_p0_use_item_command(old_state, new_state, i)
                            write_command_file(f"{command_num:03d}.txt", command)
                            command_num += 1
                    command = get_hp_command(old_state, new_state)
                    write_command_file(f"{command_num:03d}.txt", command)
                    command_num += 1

            elif new_state["game_info"]["state_name"] == "INTO_ITEM_P1_WAIT":
                if "items_p1" in changes:
                    for i in range(6):
                        if old_state["items_p1"][i] != new_state["items_p1"][i]:
                            command = get_p1_use_item_command(old_state, new_state, i)
                            write_command_file(f"{command_num:03d}.txt", command)
                            command_num += 1
                    command = get_hp_command(old_state, new_state)
                    write_command_file(f"{command_num:03d}.txt", command)
                    command_num += 1

            elif new_state["game_info"]["state_name"] == "SHOOT_INTO_P0_WAIT":
                command = get_p1_bullet_change_command(old_state, new_state)
                write_command_file(f"{command_num:03d}.txt", command)
                command_num += 1
                command = get_hp_command(old_state, new_state)
                write_command_file(f"{command_num:03d}.txt", command)
                command_num += 1

            elif new_state["game_info"]["state_name"] == "SHOOT_INTO_P1_WAIT":
                command = get_p1_bullet_change_command(old_state, new_state)
                write_command_file(f"{command_num:03d}.txt", command)
                command_num += 1
                command = get_hp_command(old_state, new_state)
                write_command_file(f"{command_num:03d}.txt", command)
                command_num += 1

            elif new_state["game_info"]["state_name"] == "SHOOT_INTO_LOAD":
                future_state = get_future_state(game_state_num + 1)
                command = get_p1_bullet_change_command(old_state, new_state, future_state)
                write_command_file(f"{command_num:03d}.txt", command)
                command_num += 1
                command = get_hp_command(old_state, new_state)
                write_command_file(f"{command_num:03d}.txt", command)

                command_num += 1

            elif new_state["game_info"]["state_name"] == "ITEM_INTO_LOAD":
                if "items_p1" in changes:
                    for i in range(6):
                        if old_state["items_p1"][i] != new_state["items_p1"][i]:
                            command = get_p1_use_item_command(old_state, new_state, i)
                            write_command_file(f"{command_num:03d}.txt", command)
                            command_num += 1
        
        old_state = new_state
        game_state_num += 1
    else:
        time.sleep(0.1)
        