# type: ignore
import pandas as pd
import json
import re
from typing import List, Dict, Any, Optional
from collections import defaultdict
from datetime import datetime
from VPIP import HeroVPIPCalculator
from FlushDraw import HeroFlushDrawCalculator

# Load the CSV file
csv_file_path = "/Users/anishrajawat/Projects/Poker_Analysis/Logs/poker_now_log_LEVIATHAN_250409.csv"

# Alternative approach using direct file reading
with open(csv_file_path, 'r') as file:
    df = pd.DataFrame([line.strip() for line in file], columns=["raw_log"])


def parse_hand(logs: List[str], hero_name: str = "LEVIATHAN") -> Dict[str, Any]:
    hand_data: Dict[str, Any] = {
        "hand_id": None,
        "timestamp": None,
        "game_type": "No Limit Texas Hold'em",
        "run_it_twice": False,
        "hero": {
            "name": hero_name,
            "position": None,
            "stack_bb": None,
            "hole_cards": None
        },
        "table": {
            "dealer": None,
            "players": [],
            "blinds": {}
        },
        "stacks_bb": {},
        "actions": {
            "preflop": [],
            "flop": {"board": [], "actions": []},
            "turn": {"board": [], "actions": []},
            "river": {"board": [], "actions": []}
        },
        "showdown": [],
        "winners": []
    }

    board_cards: Dict[str, List[str]] = {"flop": [], "turn": [], "river": []}
    current_street = "preflop"

    for line in logs:
        # Hand ID
        if "starting hand" in line:
            match = re.search(r"hand #\d+ \(id: (\w+)\)", line)
            if match:
                hand_data["hand_id"] = match.group(1)

        # Timestamp
        if not hand_data["timestamp"]:
            timestamp_match = re.search(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d+Z)", line)
            if timestamp_match:
                hand_data["timestamp"] = timestamp_match.group(1)

        # Dealer
        if "dealer:" in line: 
            dealer_match = re.search(r'dealer: ""([^"]+)""', line)
            if dealer_match:
                hand_data["table"]["dealer"] = dealer_match.group(1)

         # Blinds
        sb = re.search(r'"(.*?)" posts a small blind of (\d+)', line)
        if sb:
            hand_data["table"]["blinds"]["small_blind"] = int(sb.group(2))
        bb = re.search(r'"(.*?)" posts a big blind of (\d+)', line)
        if bb:
            hand_data["table"]["blinds"]["big_blind"] = int(bb.group(2))

        # Player Stacks
        if "Player stacks" in line:
            player_match = re.findall(r'#\d+ "(.*?)" \((\d+)\)', line)
            big_blind = hand_data["table"]["blinds"].get("big_blind", 40)
            for i, (name, stack) in enumerate(player_match):
                pos = "SB" if i == 0 else "BB" if i == 1 else f"UTG+{i-1}"  # generic positions
                stack = int(stack)
                stack_bb = round(stack / big_blind, 2)
                hand_data["table"]["players"].append({"name": name, "stack_size": stack, "position": pos})
                hand_data["stacks_bb"][name] = stack_bb
                if hero_name in name:
                    hand_data["hero"]["position"] = pos
                    hand_data["hero"]["stack_bb"] = stack_bb

        # Actions
        if "Flop:" in line:
            current_street = "flop"
            match = re.search(r"\[(.*?)\]", line)
            if match:
                hand_data["actions"]["flop"]["board"] = [card.strip() for card in match.group(1).split(",")]
        elif "Turn:" in line:
            current_street = "turn"
            match = re.search(r"\[(.*?)\]", line)
            if match:
                hand_data["actions"]["turn"]["board"] = [card.strip() for card in match.group(1).split(",")][-1:]  # Only last card
        elif "River:" in line:
            current_street = "river"
            match = re.search(r"\[(.*?)\]", line)
            if match:
                hand_data["actions"]["river"]["board"] = [card.strip() for card in match.group(1).split(",")][-1:]  # Only last card

        # Parse actions including blinds and all other actions
        blind_match = re.search(r'""(.+?)"" posts a (small|big) blind of (\d+)', line)
        if blind_match:
            action = {
                "player": blind_match.group(1),
                "action": f"posts_{blind_match.group(2)}_blind",
                "amount": int(blind_match.group(3))
            }
            hand_data["actions"]["preflop"].append(action)

        # Parse other actions (raises, calls, bets, folds, checks)
        # First try matching actions with amounts
        action_match = re.search(r'""(.+?)"" (raises to|bets|calls) (\d+)', line)
        if action_match:
            action = {
                "player": action_match.group(1),
                "action": "raises" if action_match.group(2) == "raises to" else action_match.group(2),
                "amount": int(action_match.group(3))
            }
            if "all in" in line:
                action["all_in"] = True
                
            if current_street == "preflop":
                hand_data["actions"]["preflop"].append(action)
            else:
                hand_data["actions"][current_street]["actions"].append(action)
        
        # Then try matching actions without amounts (folds, checks)
        else:
            action_match = re.search(r'""(.+?)"" (folds|checks)', line)
            if action_match:
                action = {
                    "player": action_match.group(1),
                    "action": action_match.group(2)
                }
                
                if current_street == "preflop":
                    hand_data["actions"]["preflop"].append(action)
                else:
                    hand_data["actions"][current_street]["actions"].append(action)

        # Hero hole cards
        if "Your hand" in line:
            match = re.search(r'"Your hand is ([^,]+), ([^"]+)"', line)
            if match:
                hand_data["hero"]["hole_cards"] = [match.group(1),match.group(2)]

        # Showdown cards
        show_match = re.search(r'"(.*?)" shows a (.+)', line)
        if show_match:
            hand_data["showdown"].append({
                "player": show_match.group(1),
                "hole_cards": show_match.group(2).split(", ")
            })

        # Winning hand
        win_match = re.search(r'"(.*?)" collected (\d+) from pot with (.+?) \(combination: (.+)\)', line)
        if win_match:
            name, amount, hand_desc, combo = win_match.groups()
            hand_data["winners"].append({
                "player": name,
                "amount": int(amount),
                "hand": hand_desc,
                "combo": combo.split(", ")
            })

        # Run it twice
        if "run it twice" in line:
            hand_data["run_it_twice"] = True

    return hand_data

# Process all hands in the log file
hands = []
current_hand_logs = []
for line in df["raw_log"]:
    current_hand_logs.append(line)
    if "-- starting hand" in line:   
        current_hand_logs.reverse()
        hands.append(parse_hand(current_hand_logs))
        current_hand_logs = []
    

# Add the last hand if any
if current_hand_logs:
    hands.append(parse_hand(current_hand_logs))

# Save to JSON file
json_file_path = "poker_hands.json"
with open(json_file_path, "w") as json_file:
    json.dump(hands, json_file, indent=2)

calculator = HeroVPIPCalculator(hero_name="LEVIATHAN", hands_data=hands)
vpip = calculator.process()
print(f"Hero VPIP: {vpip:.2f}%")

flush_draw_calculator = HeroFlushDrawCalculator("LEVIATHAN", hands)
flush_draw_percent = flush_draw_calculator.process()
print(f"Flush Draw on Flop (Suited Hands Only): {flush_draw_percent:.2f}%")