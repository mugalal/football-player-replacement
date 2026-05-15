import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from src.gp1.embedding_postprocessing import remove_common_components

# =====================
# PATHS
# =====================

P2VEC_PATH = "models/gp1/multi_token/player2vec.npy"
P2VEC_INDEX_PATH = "models/gp1/multi_token/player2vec_index.json"
PLAYER_NAMES_PATH = "models/gp1/shared/player_id_to_name.json"

# =====================
# LOAD DATA
# =====================


player_vectors = np.load(P2VEC_PATH)

# Remove dominant football context
player_vectors = remove_common_components(player_vectors, n_components=1)

# L2 normalize AFTER cleaning
player_vectors /= np.linalg.norm(player_vectors, axis=1, keepdims=True)


with open(P2VEC_INDEX_PATH, "r") as f:
    player_index = json.load(f)

with open(PLAYER_NAMES_PATH, "r", encoding="utf-8") as f:
    player_id_to_name = json.load(f)

player_id_to_row = {
    int(pid): i for i, pid in enumerate(player_index)
}

# =====================
# QUERY FUNCTION
# =====================

def get_similar_players(player_id, top_k=5):
    if player_id not in player_id_to_row:
        raise ValueError("Player ID not found in Player2Vec")

    idx = player_id_to_row[player_id]
    query_vec = player_vectors[idx].reshape(1, -1)

    sims = cosine_similarity(query_vec, player_vectors)[0]
    ranked = np.argsort(-sims)

    results = []
    for i in ranked[1 : top_k + 1]:  # skip self
        pid = int(player_index[i])
        results.append({
            "player_id": pid,
            "name": player_id_to_name.get(str(pid), "Unknown"),
            "similarity": float(sims[i])
        })

    return results

# =====================
# DEMO
# =====================

if __name__ == "__main__":
    query_player_id = 5203  # Player ID to query
    print(f"\nQuery Player: {player_id_to_name[str(query_player_id)]}\n")

    neighbors = get_similar_players(query_player_id, top_k=5)

    for n in neighbors:
        print(
            f"{n['name']} (ID: {n['player_id']}), similarity={n['similarity']:.3f}"
        )
