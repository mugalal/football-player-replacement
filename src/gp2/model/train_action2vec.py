import json
import multiprocessing
from gensim.models import Word2Vec

from src.gp2.paths import ACTION_SENTENCES_PATH, ACTION2VEC_PATH


class SentenceIterator:
    """
    Memory-safe iterator for large corpus
    """
    def __init__(self, file_path):
        self.file_path = file_path

    def __iter__(self):
        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                yield json.loads(line.strip())


def main():
    print("🚀 Starting Action2Vec training...")

    sentences = SentenceIterator(ACTION_SENTENCES_PATH)

    # ⚙️ SAFE CPU usage (VERY IMPORTANT)
    total_cores = multiprocessing.cpu_count()
    workers = max(1, total_cores - 2)  # leave 2 cores free

    print(f"🧠 CPU cores: {total_cores} | Using workers: {workers}")

    model = Word2Vec(
        sentences=sentences,
        vector_size=48,
        window=5,
        min_count=10,
        sg=1,                 # Skip-gram (important)
        negative=10,
        workers=workers,
        epochs=5,             # safe start
        compute_loss=True
    )

    ACTION2VEC_PATH.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(ACTION2VEC_PATH))

    print("✅ Training complete!")
    print(f"💾 Model saved to: {ACTION2VEC_PATH}")

    # 🔎 Debug: show similar tokens
    print("\n🔍 Sample token similarities:")
    print(f"Vocabulary size: {len(model.wv)}")

    # Pick actual tokens from vocabulary
    sample_tokens = list(model.wv.key_to_index.keys())[:3]

    for word in sample_tokens:
        print(f"\nTop similar to '{word}':")
        for sim_word, score in model.wv.most_similar(word, topn=5):
            print(f"  {sim_word} → {score:.4f}")


if __name__ == "__main__":
    main()
