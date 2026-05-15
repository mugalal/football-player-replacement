"""
Extract player_id → name + position from Top5 Leagues 1516 data.
Outputs a JSON file for use by run_search.py and visualization scripts.

Output format:
{
    "5246": {"name": "Luis Alberto Suárez Díaz", "position": "Center Forward"},
    "4320": {"name": "Neymar da Silva Santos Junior", "position": "Left Wing"},
    ...
}
"""

import json
from collections import defaultdict, Counter

from src.gp2.paths import PLAYER_INFO_PATH, TOP5_DATA_DIR


def main():
    print("Extracting player info from match data...")

    # Track name, position, and team occurrences per player
    player_names = {}
    player_positions = defaultdict(Counter)
    player_teams = defaultdict(Counter)

    match_count = 0

    for file in TOP5_DATA_DIR.glob("*.json"):
        with open(file, "r", encoding="utf-8") as f:
            events = json.load(f)

        for ev in events:
            player = ev.get("player")
            position = ev.get("position")
            team = ev.get("team")

            if player is None or player.get("id") is None:
                continue

            pid = str(player["id"])

            # Store name (overwrite is fine — same player same name)
            player_names[pid] = player["name"]

            # Count position occurrences to find primary position
            if position and position.get("name"):
                player_positions[pid][position["name"]] += 1
            
            # Count team occurrences to find primary team
            if team and team.get("name"):
                player_teams[pid][team["name"]] += 1

        match_count += 1
        if match_count % 200 == 0:
            print(f"Processed {match_count} matches | {len(player_names)} unique players")

    # Build final lookup — use most frequent position and team per player
    player_info = {}

    for pid, name in player_names.items():
        pos_counter = player_positions.get(pid, Counter())
        team_counter = player_teams.get(pid, Counter())
        
        primary_position = pos_counter.most_common(1)[0][0] if pos_counter else "Unknown"
        primary_team = team_counter.most_common(1)[0][0] if team_counter else "Unknown"

        player_info[pid] = {
            "name": name,
            "position": primary_position,
            "team": primary_team,
        }

    # Save
    PLAYER_INFO_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PLAYER_INFO_PATH, "w", encoding="utf-8") as f:
        json.dump(player_info, f, ensure_ascii=False, indent=2)

    print(f"\nTotal players extracted: {len(player_info)}")
    print(f"Saved to: {PLAYER_INFO_PATH}")

    # Position distribution
    positions = Counter(info["position"] for info in player_info.values())
    print(f"\nPosition distribution:")
    for pos, count in positions.most_common():
        print(f"  {pos:<30}: {count}")
    
    # Team distribution (top 20)
    teams = Counter(info["team"] for info in player_info.values())
    print(f"\nTop 20 teams by player count:")
    for team, count in teams.most_common(20):
        print(f"  {team:<30}: {count}")


if __name__ == "__main__":
    main()
