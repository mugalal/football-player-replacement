import json
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

# ============================
# CONFIG
# ============================

EVENTS_DIR = "data"
PLAYER2VEC_INDEX = "models/gp1/multi_token/player2vec_index.json"   # or single_token path
TSNE_POINTS = "models/gp1/multi_token/player2vec_tsne.npy"           # your saved tsne
PLAYER_NAME_FILE = "models/gp1/shared/player_id_to_name.json"

# ============================
# 1) POSITION MAPPING SCHEME
# ============================

POSITION_TO_ROLE = {
    "Goalkeeper": "GK",

    "Left Back": "FB", "Right Back": "FB",
    "Left Wing Back": "FB", "Right Wing Back": "FB",

    "Left Center Back": "CB", "Right Center Back": "CB",
    "Center Back": "CB",

    "Center Defensive Midfield": "DM",

    "Left Center Midfield": "CM", "Right Center Midfield": "CM",
    "Center Midfield": "CM",

    "Left Attacking Midfield": "AM", "Right Attacking Midfield": "AM",
    "Center Attacking Midfield": "AM",

    "Left Wing": "W", "Right Wing": "W",

    "Center Forward": "CF", "Striker": "CF"
}

ROLE_COLORS = {
    "GK": "gold",
    "CB": "red",
    "FB": "orangered",
    "DM": "green",
    "CM": "lime",
    "AM": "cyan",
    "W": "dodgerblue",
    "CF": "purple",
    "Unknown": "gray"
}


# ============================
# 2) LOAD PLAYER POSITIONS
# ============================

def extract_positions_from_events():
    player_position = {}

    import os
    for fname in os.listdir(EVENTS_DIR):
        if not fname.endswith(".json"):
            continue

        path = os.path.join(EVENTS_DIR, fname)

        with open(path, "r", encoding="utf-8") as f:
            events = json.load(f)

        for ev in events:
            if ev.get("type", {}).get("name") != "Starting XI":
                continue

            for pl in ev.get("tactics", {}).get("lineup", []):
                pid = pl["player"]["id"]
                pos_name = pl["position"]["name"]

                role = POSITION_TO_ROLE.get(pos_name, "Unknown")
                player_position[pid] = role

    return player_position


# ============================
# 3) LOAD PLAYER2VEC & TSNE
# ============================

with open(PLAYER2VEC_INDEX, "r") as f:
    p2v_index = json.load(f)

p2v_index = [int(x) for x in p2v_index]  # ensure ints

tsne_points = np.load(TSNE_POINTS)

with open(PLAYER_NAME_FILE, "r", encoding="utf-8") as f:
    id_to_name = json.load(f)

player_to_position = extract_positions_from_events()


# ============================
# 4) PLOT
# ============================

plt.figure(figsize=(10, 8))

for i, pid in enumerate(p2v_index):
    role = player_to_position.get(pid, "Unknown")
    color = ROLE_COLORS.get(role, "gray")

    x, y = tsne_points[i]
    plt.scatter(x, y, c=color, s=12, alpha=0.7)

# --- legend ---
for role, color in ROLE_COLORS.items():
    plt.scatter([], [], c=color, label=role)

plt.legend(title="Tactical Role", bbox_to_anchor=(1.05, 1), loc="upper left")
plt.title("t-SNE of Player2Vec Colored by Position (StatsBomb Starting-XI)")
plt.xlabel("t-SNE 1")
plt.ylabel("t-SNE 2")


# ============================
# 5) LABEL FAMOUS PLAYERS
# ============================

HIGHLIGHTS = {
    "Lionel": None,
    "Cristiano": None,
    "Neymar": None,
    "Luis": None,
    "Andrés": None,
    "Luka": None,
    "Sergio": None
}

for i, pid in enumerate(p2v_index):
    name = id_to_name.get(str(pid), "")
    for key in HIGHLIGHTS:
        if key in name:
            x, y = tsne_points[i]
            plt.text(x + 0.3, y + 0.3, name.split()[0], fontsize=9)


plt.tight_layout()
plt.show()
