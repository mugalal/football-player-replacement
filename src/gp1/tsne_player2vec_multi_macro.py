import json
import glob
import numpy as np
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE

from embedding_postprocessing import remove_common_components


P2VEC = "models/gp1/multi_token/player2vec.npy"
INDEX = "models/gp1/multi_token/player2vec_index.json"
PLAYER_ID_TO_NAME = "models/gp1/shared/player_id_to_name.json"

EVENTS_DIR = "data/*.json"

OUT_FIG = "models/gp1/multi_token/tsne_player2vec_multi_macro.png"
OUT_POINTS = "models/gp1/multi_token/tsne_player2vec_multi_macro.npy"


def infer_macro_role(position_name: str):
    """
    Convert raw StatsBomb position to GK/DEF/MID/ATT automatically.
    No external file required.
    """
    if not position_name:
        return "UNKNOWN"

    name = position_name.lower()

    if "keeper" in name:
        return "GK"

    if "back" in name or "def" in name or "center back" in name:
        return "DEF"

    if "mid" in name:
        return "MID"

    # wing, forward, striker, attacker etc.
    if "wing" in name or "forward" in name or "att" in name or "striker" in name:
        return "ATT"

    return "UNKNOWN"


def build_player_primary_position():
    """
    Build mapping:
        player_id -> most frequent position string
    directly from StatsBomb event JSON.

    This keeps you future-proof.
    """

    files = glob.glob(EVENTS_DIR)

    counts = {}

    for path in files:
        with open(path, encoding="utf-8") as f:
            events = json.load(f)

        for ev in events:
            pid = ev.get("player", {}).get("id")
            pos = ev.get("position", {}).get("name")

            if not pid or not pos:
                continue

            counts.setdefault(pid, {})
            counts[pid][pos] = counts[pid].get(pos, 0) + 1

    primary = {}

    for pid, table in counts.items():
        pos = max(table, key=table.get)
        primary[pid] = pos

    return primary


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():

    print("Loading Player2Vec…")
    X = np.load(P2VEC)

    print("Removing dominant global component…")
    X = remove_common_components(X, n_components=1)

    print("Normalizing…")
    X /= np.linalg.norm(X, axis=1, keepdims=True)

    print("Loading player index & names…")
    player_ids = load_json(INDEX)
    id2name = load_json(PLAYER_ID_TO_NAME)

    print("Extracting player primary positions from event data…")
    player_pos = build_player_primary_position()

    print("Inferring macro roles…")
    macro_roles = {}

    for pid in player_ids:
        pos_name = player_pos.get(int(pid))
        macro = infer_macro_role(pos_name)
        macro_roles[int(pid)] = macro

    print("Running t-SNE…")
    tsne = TSNE(
        n_components=2,
        perplexity=30,
        learning_rate="auto",
        init="random",
        random_state=42
    )

    Y = tsne.fit_transform(X)

    print("Saving t-SNE coordinates…")
    np.save(OUT_POINTS, Y)

    # color palette
    colors = {
        "GK": "gold",
        "DEF": "red",
        "MID": "green",
        "ATT": "blue",
        "UNKNOWN": "gray"
    }

    c = [colors[macro_roles.get(int(pid), "UNKNOWN")] for pid in player_ids]

    print("Plotting…")
    plt.figure(figsize=(10, 8))
    plt.scatter(Y[:, 0], Y[:, 1], s=8, c=c, alpha=0.8)

    plt.title("t-SNE of Player2Vec (Multi-token) — Macro Roles")
    plt.xlabel("t-SNE 1")
    plt.ylabel("t-SNE 2")

    legend_handles = [
        plt.Line2D([0], [0], marker="o", color="w", label="GK", markerfacecolor="gold", markersize=8),
        plt.Line2D([0], [0], marker="o", color="w", label="DEF", markerfacecolor="red", markersize=8),
        plt.Line2D([0], [0], marker="o", color="w", label="MID", markerfacecolor="green", markersize=8),
        plt.Line2D([0], [0], marker="o", color="w", label="ATT", markerfacecolor="blue", markersize=8),
        plt.Line2D([0], [0], marker="o", color="w", label="Unknown", markerfacecolor="gray", markersize=8),
    ]
    plt.legend(handles=legend_handles, title="Macro Role")

    plt.tight_layout()
    plt.savefig(OUT_FIG, dpi=300)
    plt.show()

    print("Done.")


if __name__ == "__main__":
    main()
