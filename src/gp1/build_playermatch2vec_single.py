import json
import numpy as np
from pathlib import Path
from collections import defaultdict

# =====================
# PATHS (single token)
# =====================

PLAY2VEC_PATH = "models/gp1/single_token/play2vec.npy"
PLAY_INDEX_PATH = "models/gp1/single_token/play2vec_index.json"
EVENTS_DIR = "data"
OUT_DIR = "models/gp1/single_token"

print("Loading Play2Vec (single token)...")
play_vectors = np.load(PLAY2VEC_PATH)

with open(PLAY_INDEX_PATH, "r") as f:
    play_index_list = json.load(f)

# Build (match, period, possession) -> embedding row id
play_index = {}
for idx, play in enumerate(play_index_list):
    match_id, period, possession, _team_id = play
    play_index[(match_id, period, possession)] = idx

print(f"Loaded {len(play_index)} plays")

player_match_plays = defaultdict(lambda: defaultdict(set))

print("Scanning raw events...")

for fname in Path(EVENTS_DIR).glob("*.json"):
    match_id = int(fname.stem)

    with open(fname, "r", encoding="utf-8") as f:
        events = json.load(f)

    for ev in events:
        if "player" not in ev:
            continue

        player_id = ev["player"]["id"]
        period = ev.get("period")
        possession = ev.get("possession")

        if period is None or possession is None:
            continue

        key = (match_id, period, possession)

        if key not in play_index:
            continue

        play_idx = play_index[key]
        player_match_plays[player_id][match_id].add(play_idx)

print(f"Found {len(player_match_plays)} players")

player_match_vectors = []
player_match_index = []

for player_id, matches in player_match_plays.items():
    for match_id, play_ids in matches.items():
        vecs = play_vectors[list(play_ids)]
        mean_vec = vecs.mean(axis=0)

        player_match_vectors.append(mean_vec)
        player_match_index.append((player_id, match_id))

player_match_vectors = np.vstack(player_match_vectors)

np.save(f"{OUT_DIR}/player_match2vec_single.npy", player_match_vectors)

with open(f"{OUT_DIR}/player_match2vec_index_single.json", "w") as f:
    json.dump(player_match_index, f)

print("PlayerMatch2Vec (single token) saved")
print("Shape:", player_match_vectors.shape)
