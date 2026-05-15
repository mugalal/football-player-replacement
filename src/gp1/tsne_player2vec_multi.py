import json
import numpy as np
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE

from embedding_postprocessing import remove_common_components

P2VEC_PATH = "models/gp1/multi_token/player2vec.npy"
P2VEC_INDEX_PATH = "models/gp1/multi_token/player2vec_index.json"
PLAYER_NAMES_PATH = "models/gp1/shared/player_id_to_name.json"

OUTPUT_FIG = "models/gp1/multi_token/tsne_player2vec_multi.png"

# =====================
# LOAD
# =====================

X = np.load(P2VEC_PATH)

# ---- optional but recommended ----
X = remove_common_components(X, n_components=1)

# normalize
X /= np.linalg.norm(X, axis=1, keepdims=True)

with open(P2VEC_INDEX_PATH) as f:
    player_ids = json.load(f)

with open(PLAYER_NAMES_PATH, encoding="utf-8") as f:
    id2name = json.load(f)

print("Running t-SNE... this can take a minute...")

tsne = TSNE(
    n_components=2,
    perplexity=30,
    learning_rate="auto",
    init="random",
    random_state=42
)

Y = tsne.fit_transform(X)

# =====================
# PLOT
# =====================

plt.figure(figsize=(10, 8))
plt.scatter(Y[:, 0], Y[:, 1], s=8, alpha=0.7)

# label some famous players
highlight = [
    "Lionel Andrés Messi Cuccittini",
    "Cristiano Ronaldo dos Santos Aveiro",
    "Sergio Busquets Burgos",
    "Neymar da Silva Santos Junior",
    "Luis Alberto Suárez Díaz",
]

for pid, (x, y) in zip(player_ids, Y):
    name = id2name.get(str(pid))
    if name in highlight:
        plt.text(x, y, name.split()[0], fontsize=8)

plt.title("t-SNE of Player2Vec (Multi-token)")
plt.tight_layout()
plt.savefig(OUTPUT_FIG, dpi=300)
plt.show()

print("Saved figure to", OUTPUT_FIG)
