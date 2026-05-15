import json
import numpy as np
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
import hdbscan

from embedding_postprocessing import remove_common_components

# =====================
# PATHS
# =====================
P2VEC_PATH = "models/gp1/multi_token/player2vec.npy"
INDEX_PATH = "models/gp1/multi_token/player2vec_index.json"
PLAYER_POS_PATH = "models/gp1/shared/player_id_to_primary_position.json"

OUT_TSNE = "models/gp1/multi_token/tsne_player2vec.npy"

# =====================
# LOAD HELPERS
# =====================
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# =====================
# MAIN
# =====================
def main():
    print("Loading Player2Vec embeddings...")
    X = np.load(P2VEC_PATH)

    print("Removing dominant global component...")
    X = remove_common_components(X, n_components=1)

    print("Normalizing vectors...")
    X /= np.linalg.norm(X, axis=1, keepdims=True)

    player_ids = load_json(INDEX_PATH)
    player_pos = load_json(PLAYER_POS_PATH)

    print("Running t-SNE...")
    tsne = TSNE(
        n_components=2,
        perplexity=30,
        init="random",
        learning_rate="auto",
        random_state=42
    )
    Y = tsne.fit_transform(X)
    np.save(OUT_TSNE, Y)

    # =====================
    # POSITION GROUPS
    # =====================
    GROUPS = {
        "Right Backs (RB + RWB)": {
            "positions": ["Right Back", "Right Wing Back"],
            "min_cluster_size": 6
        },
        "Left Backs (LB + LWB)": {
            "positions": ["Left Back", "Left Wing Back"],
            "min_cluster_size": 6
        },
        "Goalkeepers": {
            "positions": ["Goalkeeper"],
            "min_cluster_size": 4
        }
    }

    # =====================
    # CLUSTER + PLOT
    # =====================
    for title, cfg in GROUPS.items():
        indices = [
            i for i, pid in enumerate(player_ids)
            if player_pos.get(str(pid)) in cfg["positions"]
        ]

        if len(indices) < cfg["min_cluster_size"]:
            print(f"Skipping {title}: not enough samples")
            continue

        Y_sub = Y[indices]

        print(f"Clustering {title} ({len(indices)} players)...")

        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=cfg["min_cluster_size"],
            metric="euclidean"
        )
        labels = clusterer.fit_predict(Y_sub)

        plt.figure(figsize=(6, 6))
        plt.scatter(
            Y_sub[:, 0],
            Y_sub[:, 1],
            c=labels,
            cmap="tab10",
            s=40,
            edgecolors="black",
            linewidths=0.3
        )

        plt.title(f"{title} — Style Sub-Clusters")
        plt.xlabel("t-SNE 1")
        plt.ylabel("t-SNE 2")

        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        plt.text(
            0.02, 0.02,
            f"Clusters found: {n_clusters}\nNoise points: {(labels == -1).sum()}",
            transform=plt.gca().transAxes,
            fontsize=9,
            verticalalignment="bottom"
        )

        plt.tight_layout()
        plt.show()

    print("Done.")

# =====================
if __name__ == "__main__":
    main()
