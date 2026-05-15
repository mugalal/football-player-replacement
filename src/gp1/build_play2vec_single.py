import json
import numpy as np
from gensim.models import Word2Vec

ACTION2VEC_MODEL = "models/gp1/single_token/action2vec_single.model"
PLAY_SENTENCES = "models/gp1/single_token/sentences_play2vec_single.jsonl"

OUT_EMB = "models/gp1/single_token/play2vec.npy"
OUT_INDEX = "models/gp1/single_token/play2vec_index.json"

def load_sentences(path):
    plays = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            plays.append((tuple(obj["play_id"]), obj["tokens"]))
    return plays


def build_play2vec(model, plays):
    vectors = []
    index = []

    for pid, tokens in plays:
        token_vecs = [model.wv[t] for t in tokens if t in model.wv]

        if not token_vecs:
            continue

        # mean aggregation
        vec = np.mean(token_vecs, axis=0)

        vectors.append(vec)
        index.append(pid)

    return np.vstack(vectors), index


def main():
    print("Loading Action2Vec...")
    model = Word2Vec.load(ACTION2VEC_MODEL)

    print("Loading plays...")
    plays = load_sentences(PLAY_SENTENCES)

    print("Building Play2Vec...")
    X, idx = build_play2vec(model, plays)

    print("Saving...")
    np.save(OUT_EMB, X)

    with open(OUT_INDEX, "w", encoding="utf-8") as f:
        json.dump([list(x) for x in idx], f)

    print("Done.")


if __name__ == "__main__":
    main()
