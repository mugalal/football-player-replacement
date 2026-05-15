import json
import glob
from collections import Counter, defaultdict

DATA_DIR = "data"
OUT_PATH = "models/gp1/shared/player_id_to_primary_position.json"

def main():
    player_positions = defaultdict(Counter)

    files = glob.glob(f"{DATA_DIR}/*.json")
    print(f"Scanning {len(files)} match files...")

    for path in files:
        with open(path, encoding="utf-8") as f:
            events = json.load(f)

        for ev in events:
            player = ev.get("player")
            position = ev.get("position")

            if player and position:
                pid = str(player["id"])
                pos_name = position["name"]
                player_positions[pid][pos_name] += 1

    # majority vote
    player_primary_pos = {
        pid: counter.most_common(1)[0][0]
        for pid, counter in player_positions.items()
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(player_primary_pos, f, indent=2, ensure_ascii=False)

    print(f"Saved primary positions for {len(player_primary_pos)} players")
    print(f"Output -> {OUT_PATH}")

if __name__ == "__main__":
    main()
