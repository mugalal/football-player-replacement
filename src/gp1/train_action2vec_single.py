import json
from gensim.models import Word2Vec

INPUT_SENTENCES = "models/gp1/single_token/sentences_action2vec_single.jsonl"
OUT_MODEL = "models/gp1/single_token/action2vec_single.model"

EMBEDDING_DIM = 100
WINDOW = 10
MIN_COUNT = 5
WORKERS = 4

def load_sentences(path):
    sentences = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            toks = json.loads(line)
            sentences.append(toks)
    return sentences


def main():
    print("Loading sentences...")
    sents = load_sentences(INPUT_SENTENCES)
    print(f"Loaded {len(sents)} sentences")

    print("Training Word2Vec...")
    model = Word2Vec(
        sentences=sents,
        vector_size=EMBEDDING_DIM,
        window=WINDOW,
        min_count=MIN_COUNT,
        workers=WORKERS,
        sg=1
    )

    print("Saving model...")
    model.save(OUT_MODEL)
    print("Done.")


if __name__ == "__main__":
    main()
