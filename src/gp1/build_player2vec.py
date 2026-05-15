import json
import numpy as np
from collections import defaultdict

# =====================
# PATHS
# =====================

PM2VEC_PATH = "models/gp1/multi_token/player_match2vec.npy"
PM_INDEX_PATH = "models/gp1/multi_token/player_match2vec_index.json"
OUT_DIR = "models/gp1/multi_token/"

# =====================
# LOAD PLAYER-MATCH VECTORS
# =====================

print("Loading PlayerMatch2Vec...")

player_match_vectors = np.load(PM2VEC_PATH)

with open(PM_INDEX_PATH, "r") as f:
    player_match_index = json.load(f)

assert len(player_match_vectors) == len(player_match_index)

print(f"Loaded {len(player_match_index)} player-match vectors")

# =====================
# GROUP BY PLAYER
# =====================

player_vectors = defaultdict(list)

for vec, (player_id, _match_id) in zip(player_match_vectors, player_match_index):
    player_vectors[player_id].append(vec)

print(f"Found {len(player_vectors)} unique players")

# =====================
# AGGREGATE (MEAN)
# =====================

player2vec = []
player2vec_index = []

for player_id, vecs in player_vectors.items():
    mean_vec = np.mean(vecs, axis=0)
    player2vec.append(mean_vec)
    player2vec_index.append(player_id)

player2vec = np.vstack(player2vec)

# =====================
# SAVE
# =====================

np.save(f"{OUT_DIR}/player2vec.npy", player2vec)

with open(f"{OUT_DIR}/player2vec_index.json", "w") as f:
    json.dump(player2vec_index, f)

print("Player2Vec saved")
print("Shape:", player2vec.shape)
