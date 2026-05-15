import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from embedding_postprocessing import remove_common_components

# =====================
# PATHS (single token)
# =====================

P2VEC_PATH = "models/gp1/single_token/player2vec_single.npy"
P2VEC_INDEX_PATH = "models/gp1/single_token/player2vec_index_single.json"
PLAYER_NAMES_PATH = "models/gp1/shared/player_id_to_name.json"

# =====================
# LOAD
# =====================

player_vectors = np.load(P2VEC_PATH)

# ---- OPTIONAL BUT RECOMMENDED ----
# Remove dominant context
player_vectors = remove_common_components(player_vectors, n_components=1)

# Normalize
player_vectors /= np.linalg.norm(player_vectors, axis=1, keepdims=True)

with open(P2VEC_INDEX_PATH, "r") as f:
    player_index = json.load(f)

with open(PLAYER_NAMES_PATH, "r", encoding="utf-8") as f:
    player_id_to_name = json.load(f)

player_id_to_row = {int(pid): i for i, pid in enumerate(player_index)}


# =====================
# QUERY FUNCTION
# =====================

def get_similar_players_single(player_id, top_k=5):
    if player_id not in player_id_to_row:
        raise ValueError("Player ID not found in Player2Vec (single token)")

    idx = player_id_to_row[player_id]
    query_vec = player_vectors[idx:idx+1]

    sims = cosine_similarity(query_vec, player_vectors)[0]
    ranked = np.argsort(-sims)

    neighbors = []
    for i in ranked[1: top_k + 1]:
        pid = int(player_index[i])
        neighbors.append({
            "player_id": pid,
            "name": player_id_to_name.get(str(pid), "Unknown"),
            "similarity": float(sims[i])
        })

    return neighbors


# =====================
# DEMO
# =====================

if __name__ == "__main__":
    query_player_id = 5216  # example

    print("\nSingle-token Player2Vec similarity search")
    print("-----------------------------------------")
    print(f"Query Player: {player_id_to_name.get(str(query_player_id), 'Unknown')}")

    for n in get_similar_players_single(query_player_id, top_k=5):
        print(f"{n['name']} (ID: {n['player_id']}), similarity={n['similarity']:.3f}")
