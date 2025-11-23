"""
Play Buckshot Roulette against the trained AI
You are P1, AI is P2
"""

import numpy as np
from sb3_contrib import MaskablePPO
from buckshot_env import BuckshotEnv
from game_state import GameState


class HumanPlayer:
    """Human player interface"""

    def __init__(self, player_name="P1"):
        self.player_name = player_name
        self.action_names = [
            "Shoot Enemy",
            "Shoot Self",
            "Use Magnifier",
            "Use Cigarette",
            "Use Beer",
            "Use Saw",
            "Use Handcuff",
            "Use Phone",
            "use Reverse"
            "Ready"
        ]

    def show_game_state(self, gs, player_state):
        """Display current game state"""
        print("\n" + "="*70)
        print(f"HP: You(P1)={gs.p1.hp} | AI(P2)={gs.p2.hp}")
        print(f"Bullets: {gs.live_left} live, {gs.blank_left} blank "
              f"({len(gs.real_bullets) - gs.current_index} remaining)")

        # Show your items
        items = player_state.items
        print(f"\nYour Items:")
        print(f"  [2] Magnifier: {items.magnifier}")
        print(f"  [3] Cigarette: {items.cigarette} (+1 HP)")
        print(f"  [4] Beer: {items.beer} (remove current bullet)")
        print(f"  [5] Saw: {items.saw} (2x damage)")
        print(f"  [6] Handcuff: {items.handcuff} (skip opponent turn)")
        print(f"  [7] Phone: {items.phone} (reveal random bullet)")
        print(f"  [8] Reverse: {items.reverse} (swap bullets with opponent)")
        print(f"  [9] Ready")
        
        # Show your knowledge
        known = [(i, b) for i, b in enumerate(player_state.bullet_knowledge) if b is not None]
        if known:
            print(f"\nYou Know:")
            for idx, bullet in known:
                print(f"  Bullet #{idx}: {bullet.upper()}")

        print("="*70)

    def get_action(self, gs, player_state, phase):
        """Get action from human player"""
        while True:
            if phase == "item":
                print("\n[YOUR TURN - ITEM PHASE]")
                print("Available actions:")
                print("  [2-7] Use item (see numbers above)")
                print("  [8] Ready (go to shoot phase)")

                try:
                    choice = input("\nEnter action number: ").strip()
                    action = int(choice)

                    if action == 8:
                        return action
                    elif 2 <= action <= 7:
                        # Check if player has this item
                        item_names = ["magnifier", "cigarette", "beer", "saw", "handcuff", "phone"]
                        item = item_names[action - 2]
                        if getattr(player_state.items, item) > 0:
                            return action
                        else:
                            print(f"❌ You don't have {item}!")
                    else:
                        print("❌ Invalid action! Use 2-7 for items, 8 for ready.")

                except (ValueError, IndexError):
                    print("❌ Invalid input! Enter a number.")

            elif phase == "shoot":
                print("\n[YOUR TURN - SHOOT PHASE]")
                print("Available actions:")
                print("  [0] Shoot Enemy (AI)")
                print("  [1] Shoot Self")

                try:
                    choice = input("\nEnter action number: ").strip()
                    action = int(choice)

                    if action in [0, 1]:
                        return action
                    else:
                        print("❌ Invalid action! Use 0 or 1.")

                except ValueError:
                    print("❌ Invalid input! Enter 0 or 1.")


def play_against_ai(model_path):
    """Play a game against the AI"""
    print("="*70)
    print("BUCKSHOT ROULETTE - Human vs AI")
    print("="*70)
    print(f"Loading AI model: {model_path}")

    # Load AI model
    model = MaskablePPO.load(model_path)
    print("✓ AI model loaded!\n")

    # Create environment (AI plays as P2)
    env = BuckshotEnv(opponent_model=None, verbose=False)

    # Create human player
    human = HumanPlayer("P1")

    # Action names for AI
    ai_action_names = [
        "Shoot Enemy", "Shoot Self",
        "Use Magnifier", "Use Cigarette", "Use Beer",
        "Use Saw", "Use Handcuff", "Use Phone",
        "Ready"
    ]

    print("="*70)
    print("GAME RULES:")
    print("- You are P1, AI is P2")
    print("- Take turns using items and shooting")
    print("- Shoot self with BLANK = extra turn")
    print("- Reduce opponent to 0 HP to win")
    print("="*70)
    input("\nPress Enter to start...")

    # Start game
    obs, _ = env.reset()
    gs = env.gs
    done = False

    # Game loop
    while not done:
        # P1's turn (human)
        if gs.turn == "p1":
            # Item phase
            while gs.phase == "item" and gs.turn == "p1":
                human.show_game_state(gs, gs.p1)
                action = human.get_action(gs, gs.p1, "item")

                if action == 8:  # Ready
                    gs.phase = "shoot"
                    print("\n→ You are ready to shoot!")
                elif 2 <= action <= 7:
                    # Use item
                    item_names = ["magnifier", "cigarette", "beer", "saw", "handcuff", "phone"]
                    item = item_names[action - 2]

                    # Manually apply item
                    env._use_item(gs.p1, gs.p2, gs, item)
                    setattr(gs.p1.items, item, getattr(gs.p1.items, item) - 1)

                    print(f"\n→ You used {item.upper()}!")

                    # Show result for magnifier/beer/phone
                    if item == "magnifier":
                        if gs.current_index < len(gs.real_bullets):
                            bullet = gs.p1.bullet_knowledge[gs.current_index]
                            print(f"   Next bullet: {bullet.upper()}")
                    elif item == "beer":
                        print(f"   Removed bullet")
                    elif item == "phone":
                        known = [i for i, b in enumerate(gs.p1.bullet_knowledge) if b is not None]
                        if known:
                            print(f"   You know bullet positions: {known}")

            # Shoot phase
            if gs.phase == "shoot" and gs.turn == "p1":
                human.show_game_state(gs, gs.p1)
                action = human.get_action(gs, gs.p1, "shoot")

                if action == 0:  # Shoot enemy
                    print("\n→ You shoot the AI!")
                    env._shoot(gs, gs.p1, gs.p2, target="enemy")
                elif action == 1:  # Shoot self
                    print("\n→ You shoot yourself!")
                    env._shoot(gs, gs.p1, gs.p1, target="self")

                # Check if bullets ran out
                if gs.current_index >= len(gs.real_bullets):
                    print("\n🔄 Magazine empty! Loading new round...")
                    env._load_new_round()

                # Check if game ended
                if gs.p1.hp <= 0 or gs.p2.hp <= 0:
                    done = True
                    break

        # P2's turn (AI)
        else:
            print("\n" + "="*70)
            print("[AI'S TURN]")
            print("="*70)

            # Handle handcuff
            if gs.p2.handcuffed:
                print("AI is handcuffed! Turn skipped.")
                gs.p2.handcuffed = False
                gs.turn = "p1"
                gs.phase = "item"
                input("\nPress Enter to continue...")
                continue

            # AI item phase
            max_items = 10
            items_used = 0
            while gs.phase == "item" and gs.turn == "p2" and items_used < max_items:
                # Get AI action
                action_mask = env.action_masks()
                obs = env.encoder.encode(gs)
                action, _ = model.predict(obs, action_masks=action_mask, deterministic=False)

                print(f"AI: {ai_action_names[action]}")

                if action == 8:  # Ready
                    gs.phase = "shoot"
                    break
                elif 2 <= action <= 7:
                    # Use item
                    item_idx = action - 2
                    item_names = ["magnifier", "cigarette", "beer", "saw", "handcuff", "phone"]
                    item = item_names[item_idx]

                    if getattr(gs.p2.items, item) > 0:
                        env._use_item(gs.p2, gs.p1, gs, item)
                        setattr(gs.p2.items, item, getattr(gs.p2.items, item) - 1)
                        items_used += 1
                    else:
                        gs.phase = "shoot"
                        break
                else:
                    gs.phase = "shoot"
                    break

            # AI shoot phase
            if gs.phase == "shoot" and gs.turn == "p2":
                # Check bullets
                if gs.current_index >= len(gs.real_bullets):
                    print("\n🔄 Magazine empty! Loading new round...")
                    env._load_new_round()
                    input("\nPress Enter to continue...")
                    continue

                # Get AI action
                action_mask = env.action_masks()
                obs = env.encoder.encode(gs)
                action, _ = model.predict(obs, action_masks=action_mask, deterministic=False)

                print(f"AI: {ai_action_names[action]}")

                if action == 0:  # Shoot enemy (you)
                    env._shoot(gs, gs.p2, gs.p1, target="enemy")
                elif action == 1:  # Shoot self
                    env._shoot(gs, gs.p2, gs.p2, target="self")

                # Check if bullets ran out
                if gs.current_index >= len(gs.real_bullets):
                    print("\n🔄 Magazine empty! Loading new round...")
                    env._load_new_round()

                # Check if game ended
                if gs.p1.hp <= 0 or gs.p2.hp <= 0:
                    done = True

            input("\nPress Enter to continue...")

    # Game over
    print("\n" + "="*70)
    print("GAME OVER")
    print("="*70)
    print(f"Final HP: You(P1)={gs.p1.hp} | AI(P2)={gs.p2.hp}")

    if gs.p1.hp > 0 and gs.p2.hp <= 0:
        print("\n🎉 YOU WIN!")
    else:
        print("\n💀 AI WINS!")
    print("="*70)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Play Buckshot Roulette against trained AI")
    parser.add_argument("model", type=str, help="Path to trained model (e.g., models/buckshot_final)")

    args = parser.parse_args()

    try:
        play_against_ai(args.model)
    except KeyboardInterrupt:
        print("\n\nGame interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
