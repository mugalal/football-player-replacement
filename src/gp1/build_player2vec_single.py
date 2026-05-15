import json
import numpy as np
from collections import defaultdict

PM2VEC_PATH = "models/gp1/single_token/player_match2vec_single.npy"
PM_INDEX_PATH = "models/gp1/single_token/player_match2vec_index_single.json"
OUT_DIR = "models/gp1/single_token"

print("Loading PlayerMatch2Vec (single token)...")

player_match_vectors = np.load(PM2VEC_PATH)

with open(PM_INDEX_PATH, "r") as f:
    player_match_index = json.load(f)

assert len(player_match_vectors) == len(player_match_index)

print(f"Loaded {len(player_match_index)} player-match vectors")

player_vectors = defaultdict(list)

for vec, (player_id, _match_id) in zip(player_match_vectors, player_match_index):
    player_vectors[player_id].append(vec)

print(f"Found {len(player_vectors)} unique players")

player2vec = []
player2vec_index = []

for player_id, vecs in player_vectors.items():
    mean_vec = np.mean(vecs, axis=0)
    player2vec.append(mean_vec)
    player2vec_index.append(player_id)

player2vec = np.vstack(player2vec)

np.save(f"{OUT_DIR}/player2vec_single.npy", player2vec)

with open(f"{OUT_DIR}/player2vec_index_single.json", "w") as f:
    json.dump(player2vec_index, f)

print("Player2Vec (single token) saved")
print("Shape:", player2vec.shape)
