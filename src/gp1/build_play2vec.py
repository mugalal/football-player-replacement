# src/build_play2vec.py

import json
import numpy as np
from pathlib import Path
from gensim.models import Word2Vec


# =====================
# CONFIG
# =====================

ACTION2VEC_PATH = "models/gp1/multi_token/action2vec.model"
PLAY_SENTENCES_PATH = "models/gp1/multi_token/sentences_play2vec.jsonl"

OUT_EMB_PATH = "models/gp1/multi_token/play2vec.npy"
OUT_INDEX_PATH = "models/gp1/multi_token/play2vec_index.json"


# =====================
# LOADERS
# =====================

def load_play_sentences(path):
    plays = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            plays.append((tuple(obj["play_id"]), obj["tokens"]))
    return plays


# =====================
# PLAY2VEC BUILDER
# =====================

def build_play2vec(action_model, plays):
    vectors = []
    index = []

    for play_id, tokens in plays:
        token_vecs = []

        for t in tokens:
            if t in action_model.wv:
                token_vecs.append(action_model.wv[t])

        if not token_vecs:
            continue  # skip empty / invalid plays

        play_vec = np.mean(token_vecs, axis=0)
        vectors.append(play_vec)
        index.append(play_id)

    return np.vstack(vectors), index


# =====================
# MAIN
# =====================

def main():
    print("Loading Action2Vec model...")
    action_model = Word2Vec.load(ACTION2VEC_PATH)

    print("Loading play sentences...")
    plays = load_play_sentences(PLAY_SENTENCES_PATH)
    print(f"Loaded {len(plays)} plays")

    print("Building Play2Vec embeddings...")
    play_vectors, play_index = build_play2vec(action_model, plays)

    print(f"Final Play2Vec shape: {play_vectors.shape}")

    print("Saving outputs...")
    np.save(OUT_EMB_PATH, play_vectors)

    with open(OUT_INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(play_index, f)

    print("Play2Vec saved successfully")


if __name__ == "__main__":
    main()
