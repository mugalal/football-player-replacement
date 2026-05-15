"""
Action2Vec Training
-------------------

- Trains Word2Vec on possession-level action token sequences
- Input: models/sentences.jsonl
- Output: models/action2vec.model

Author: Omar Sameh
Reference: Ofir Magdaci – football2vec
"""

import json
from gensim.models import Word2Vec
from pathlib import Path

# =====================
# CONFIG
# =====================

SENTENCES_PATH = "models/gp1/multi_token/sentences.jsonl"
MODEL_OUT = "models/gp1/multi_token/action2vec.model"

VECTOR_SIZE = 100
WINDOW_SIZE = 5
MIN_COUNT = 3
EPOCHS = 15
SG = 1  # Skip-gram

# =====================
# LOAD SENTENCES
# =====================

def load_sentences(path):
    sentences = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            sentences.append(json.loads(line))
    return sentences


# =====================
# MAIN
# =====================

def main():
    print("Loading possession sentences...")
    sentences = load_sentences(SENTENCES_PATH)
    print(f"Loaded {len(sentences):,} sentences")

    print("\nTraining Action2Vec (Word2Vec)...")
    model = Word2Vec(
        sentences=sentences,
        vector_size=VECTOR_SIZE,
        window=WINDOW_SIZE,
        min_count=MIN_COUNT,
        sg=SG,
        negative=5,
        workers=4,
        epochs=EPOCHS
    )

    print("\nSaving model...")
    Path(MODEL_OUT).parent.mkdir(parents=True, exist_ok=True)
    model.save(MODEL_OUT)

    print(f"Model saved to {MODEL_OUT}")
    print("\nVocabulary size:", len(model.wv))


if __name__ == "__main__":
    main()
