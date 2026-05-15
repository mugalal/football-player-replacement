import json
from pathlib import Path

DATA_DIR = "data"
OUT_PATH = "models/gp1/shared/player_id_to_name.json"

player_id_to_name = {}

for fname in Path(DATA_DIR).glob("*.json"):
    with open(fname, "r", encoding="utf-8") as f:
        events = json.load(f)

    for ev in events:
        if "player" in ev:
            pid = ev["player"]["id"]
            name = ev["player"]["name"]
            if pid not in player_id_to_name:
                player_id_to_name[pid] = name

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(player_id_to_name, f, ensure_ascii=False, indent=2)

print(f"Saved {len(player_id_to_name)} player names → {OUT_PATH}")
