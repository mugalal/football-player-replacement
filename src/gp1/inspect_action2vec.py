"""
Action2Vec Sanity Checks
-----------------------

- Loads trained Action2Vec model
- Inspects nearest neighbors for key football tokens
- Used to validate semantic quality of embeddings

Author: Omar Sameh
"""

from gensim.models import Word2Vec

# =====================
# CONFIG
# =====================

MODEL_PATH = "models/gp1/multi_token/action2vec.model"

TOKENS_TO_CHECK = [
    "pass",
    "pass_short",
    "pass_long",
    "carry",
    "shot",
    "duel",
    "pressure",
    "pass_zone_10",
    "pass_zone_14"
]

TOP_N = 10


# =====================
# HELPERS
# =====================

def inspect_neighbors(model, token, topn=10):
    if token not in model.wv:
        print(f"\nToken '{token}' not in vocabulary.")
        return

    print(f"\nNearest neighbors for '{token}':")
    for word, score in model.wv.most_similar(token, topn=topn):
        print(f"  {word:<30} {score:.3f}")


# =====================
# MAIN
# =====================

def main():
    print("Loading Action2Vec model...")
    model = Word2Vec.load(MODEL_PATH)
    print(f"Model loaded. Vocabulary size: {len(model.wv)}")

    for token in TOKENS_TO_CHECK:
        inspect_neighbors(model, token, TOP_N)


if __name__ == "__main__":
    main()
