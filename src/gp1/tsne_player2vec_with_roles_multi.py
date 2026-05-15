import json
import numpy as np
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE

from embedding_postprocessing import remove_common_components

# ===============================
# PATHS
# ===============================
P2VEC_PATH = "models/gp1/multi_token/player2vec.npy"
INDEX_PATH = "models/gp1/multi_token/player2vec_index.json"
PLAYER_POS_PATH = "models/gp1/shared/player_id_to_primary_position.json"

OUT_TSNE = "models/gp1/multi_token/tsne_player2vec_multi_positions.npy"
OUT_FIG = "models/gp1/multi_token/tsne_player2vec_multi_positions_grouped.png"

# ===============================
# UTILITIES
# ===============================
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ===============================
# POSITION → TACTICAL GROUP
# ===============================
def map_position_to_group(pos: str) -> str:
    p = pos.lower()

    # Goalkeeper
    if "goalkeeper" in p:
        return "GK"

    # Center backs (LCB, RCB, CB)
    if "center back" in p or p == "center back":
        return "CB"

    # Fullbacks / Wingbacks
    if "right back" in p or "right wing back" in p:
        return "RB"
    if "left back" in p or "left wing back" in p:
        return "LB"

    # Defensive midfield
    if "defensive midfield" in p:
        return "DM"

    # Central midfield
    if "center midfield" in p:
        return "CM"

    # Attacking midfield
    if "attacking midfield" in p:
        return "AM"
    # Right midfield
    if "right midfield" in p:
        return "RM"
    
    # Left midfield
    if "left midfield" in p:
        return "LM"

    # Wingers
    if "wing" in p:
        return "W"

    # Forwards
    if "center forward" in p or "striker" in p:
        return "CF"

    return "Other"

# ===============================
# COLORS (HIGH CONTRAST)
# ===============================
GROUP_COLORS = {
    "GK": "#FFD700",      # gold
    "CB": "#FF0000",      # red
    "RB": "#FF7700",      # orange
    "LB": "#0004FF",      # blue
    "DM": "#00FF00",      # green
    "CM": "#00E5FF",      # cyan
    "AM": "#8400FF",      # purple
    "W":  "#FF8870",      # brown
    "CF": "#FF00B3",      # pink
    "RM": "#000000",    
    "LM": "#7F7F7F",
    "Other": "#7F7F7F"     # gray
}

# ===============================
# MAIN
# ===============================
def main():
    print("Loading Player2Vec embeddings...")
    X = np.load(P2VEC_PATH)

    print("Removing dominant global component...")
    X = remove_common_components(X, n_components=1)

    print("Normalizing embeddings...")
    X /= np.linalg.norm(X, axis=1, keepdims=True)

    print("Loading indices and positions...")
    player_ids = load_json(INDEX_PATH)
    player_primary_pos = load_json(PLAYER_POS_PATH)

    print(f"Players: {len(player_ids)}")

    print("Running t-SNE...")
    tsne = TSNE(
        n_components=2,
        perplexity=30,
        learning_rate="auto",
        init="random",
        random_state=42
    )
    Y = tsne.fit_transform(X)

    np.save(OUT_TSNE, Y)

    # ===============================
    # ASSIGN GROUPS
    # ===============================
    groups = []
    colors = []

    for pid in player_ids:
        pos = player_primary_pos.get(str(pid), "Unknown")
        group = map_position_to_group(pos)
        groups.append(group)
        colors.append(GROUP_COLORS[group])

    print("Plotting t-SNE...")
    plt.figure(figsize=(12, 9))
    plt.scatter(Y[:, 0], Y[:, 1], c=colors, s=18, alpha=0.85)

    plt.title("t-SNE of Player2Vec (Multi-token) — Grouped Tactical Positions")
    plt.xlabel("t-SNE 1")
    plt.ylabel("t-SNE 2")

    # Legend
    handles = [
        plt.Line2D(
            [0], [0],
            marker="o",
            color="w",
            label=k,
            markerfacecolor=v,
            markersize=8
        )
        for k, v in GROUP_COLORS.items()
    ]
    plt.legend(handles=handles, title="Tactical Group", loc="best")

    plt.tight_layout()
    plt.savefig(OUT_FIG, dpi=300)
    plt.show()

    print(f"Saved figure to {OUT_FIG}")
    print("Done.")

if __name__ == "__main__":
    main()
