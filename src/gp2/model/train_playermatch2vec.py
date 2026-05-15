"""
Train Separate On-Ball and Off-Ball Doc2Vec Models — V2

V2 Changes:
    - Onball Doc2Vec:  48D (inherits word vectors from Action2Vec)
    - Offball Doc2Vec: 16D (trains from scratch — no inheritance, dimensions don't match)

Why asymmetric dimensions:
    - On-ball events are 3-5x more frequent → richer signal → more dimensions
    - Off-ball events are sparser but distinctive → 16D is enough
    - Total concatenated: 64D (same as before)

Output:
    - playermatch2vec_onball.model  (48D)
    - playermatch2vec_offball.model (16D)
"""

import json
import multiprocessing
from pathlib import Path

from gensim.models import Word2Vec
from gensim.models.doc2vec import Doc2Vec, TaggedDocument

from src.gp2.paths import (
    ACTION2VEC_PATH,
    OFFBALL_MODEL_PATH,
    ONBALL_MODEL_PATH,
    PLAYER_MATCH_DOCS_PATH,
)


# ==================================================================================================
# DIMENSIONS — V2 ASYMMETRIC
# ==================================================================================================

ONBALL_DIM = 48      # Inherits from Action2Vec (must match Action2Vec dim)
OFFBALL_DIM = 16     # Trains from scratch (no inheritance)


# ==================================================================================================
# DOCUMENT ITERATORS
# ==================================================================================================

class OnBallIterator:
    """Streams on-ball documents only."""

    def __init__(self, file_path):
        self.file_path = file_path

    def __iter__(self):
        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                doc = json.loads(line.strip())
                if not doc.get("onball_tokens"):
                    continue
                tag = f"{doc['player_id']}_{doc['match_id']}"
                yield TaggedDocument(words=doc["onball_tokens"], tags=[tag])


class OffBallIterator:
    """Streams off-ball documents only."""

    def __init__(self, file_path):
        self.file_path = file_path

    def __iter__(self):
        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                doc = json.loads(line.strip())
                if not doc.get("offball_tokens"):
                    continue
                tag = f"{doc['player_id']}_{doc['match_id']}"
                yield TaggedDocument(words=doc["offball_tokens"], tags=[tag])


# ==================================================================================================
# TRAINING
# ==================================================================================================

def train_doc2vec_model(iterator, model_path, name, vector_size, action2vec=None):
    """
    Train one Doc2Vec model.

    Args:
        iterator:        OnBallIterator or OffBallIterator
        model_path:      where to save the trained model
        name:            display name for logging
        vector_size:     dimensionality of doc vectors
        action2vec:      optional Word2Vec model to inherit word vectors from.
                         Must have matching vector_size or inheritance is skipped.
    """
    print(f"\n{'='*80}")
    print(f"Training {name} Model — {vector_size}D")
    print(f"{'='*80}")

    # Count documents (iterator re-opens file each time, so this is safe)
    doc_count = sum(1 for _ in iterator)
    print(f"Total documents: {doc_count:,}")

    # CPU safety
    total_cores = multiprocessing.cpu_count()
    workers = max(1, total_cores - 2)
    print(f"CPU cores: {total_cores} | Using workers: {workers}")

    # Build Doc2Vec model
    model = Doc2Vec(
        vector_size=vector_size,
        window=2,
        min_count=5,
        dm=1,
        negative=10,
        workers=workers,
        epochs=20,
    )

    # Build vocabulary
    print("Building vocabulary...")
    model.build_vocab(iterator)
    print(f"Vocabulary: {len(model.wv)} tokens")

    # Inherit word vectors from Action2Vec (if dimensions match)
    if action2vec is not None:
        if action2vec.wv.vector_size != vector_size:
            print(
                f"⚠ Action2Vec dim ({action2vec.wv.vector_size}) != Doc2Vec dim ({vector_size}). "
                f"Skipping inheritance — will train from scratch."
            )
        else:
            copied = 0
            for word in model.wv.key_to_index:
                if word in action2vec.wv:
                    model.wv[word] = action2vec.wv[word]
                    copied += 1
            print(f"Copied {copied}/{len(model.wv)} word vectors from Action2Vec")
    else:
        print("No Action2Vec inheritance — training word vectors from scratch")

    # Train
    print("Training...")
    model.train(
        iterator,
        total_examples=model.corpus_count,
        epochs=model.epochs,
    )

    # Save
    Path(model_path).parent.mkdir(parents=True, exist_ok=True)
    model.save(str(model_path))
    print(f"Saved to: {model_path}")

    return model


def main():
    print("=" * 80)
    print("TRAINING ASYMMETRIC ON-BALL / OFF-BALL DOC2VEC MODELS (V2)")
    print("=" * 80)
    print(f"\nArchitecture:")
    print(f"  On-ball  Doc2Vec: {ONBALL_DIM}D (inherits from Action2Vec)")
    print(f"  Off-ball Doc2Vec: {OFFBALL_DIM}D (from scratch)")
    print(f"  Final concat:     {ONBALL_DIM + OFFBALL_DIM}D")

    # Load pretrained Action2Vec
    print(f"\nLoading Action2Vec from: {ACTION2VEC_PATH}")
    action2vec = Word2Vec.load(str(ACTION2VEC_PATH))
    print(f"Action2Vec vocabulary: {len(action2vec.wv)} tokens, dim: {action2vec.wv.vector_size}")

    # Sanity check: Action2Vec must match ONBALL_DIM for inheritance to work
    if action2vec.wv.vector_size != ONBALL_DIM:
        print(
            f"\n⚠ WARNING: Action2Vec dim ({action2vec.wv.vector_size}) != ONBALL_DIM ({ONBALL_DIM}). "
            f"On-ball model will train from scratch instead of inheriting."
        )

    # Train on-ball model (with inheritance)
    onball_iter = OnBallIterator(PLAYER_MATCH_DOCS_PATH)
    train_doc2vec_model(
        iterator=onball_iter,
        model_path=ONBALL_MODEL_PATH,
        name="On-Ball",
        vector_size=ONBALL_DIM,
        action2vec=action2vec,
    )

    # Train off-ball model (no inheritance — different dimensionality)
    offball_iter = OffBallIterator(PLAYER_MATCH_DOCS_PATH)
    train_doc2vec_model(
        iterator=offball_iter,
        model_path=OFFBALL_MODEL_PATH,
        name="Off-Ball",
        vector_size=OFFBALL_DIM,
        action2vec=None,
    )

    print("\n" + "=" * 80)
    print("TRAINING COMPLETE")
    print("=" * 80)
    print(f"\nOn-ball model:  {ONBALL_MODEL_PATH}  ({ONBALL_DIM}D)")
    print(f"Off-ball model: {OFFBALL_MODEL_PATH} ({OFFBALL_DIM}D)")
    print(f"\nNext step: Run build_player2vec.py to create {ONBALL_DIM + OFFBALL_DIM}D Player2Vec")


if __name__ == "__main__":
    main()
