import os
import json
import numpy as np
import random
import torch
from src.preprocess.tokens import event_to_tokens
from src.preprocess.sequence_builder import build_possession_sequences
from src.model.extract_embeddings import extract_embeddings
from src.model.train import train_model
from src.model.similarity import find_similar_players
from collections import Counter
import torch.nn.functional as F
from src.preprocess.prepare_sequences import (
    flatten_sequences,
    build_vocab,
    encode_sequences,
    pad_sequences
)

DATA_DIR = "data"
MAX_MATCHES = None   # 🔥 change to None to use ALL matches


def load_matches(data_dir, max_matches=None):
    files = [f for f in os.listdir(data_dir) if f.endswith(".json")]
    random.shuffle(files)
    if max_matches:
        files = files[:max_matches]

    all_events = []

    for file in files:
        path = os.path.join(data_dir, file)
        with open(path, "r", encoding="utf-8") as f:
            events = json.load(f)
            all_events.extend(events)

    return all_events


# 1. Load data
events = load_matches(DATA_DIR, MAX_MATCHES)

print(f"Loaded events: {len(events)}")

# 2. Build sequences
sequences = build_possession_sequences(events, event_to_tokens)

# 3. Flatten
flat_sequences, player_ids = flatten_sequences(sequences)

# 4. Vocab
vocab = build_vocab(flat_sequences)

# 5. Encode
encoded = encode_sequences(flat_sequences, vocab)

# 6. Length stats (IMPORTANT 🔥)
lengths = [len(seq) for seq in flat_sequences]

print("\n--- LENGTH STATS ---")
print("Min:", min(lengths))
print("Max:", max(lengths))
print("Avg:", sum(lengths)/len(lengths))
print("95th percentile:", int(np.percentile(lengths, 95)))

# 7. Padding (temporary value for now)
MAX_LEN = int(np.percentile(lengths, 95))
padded = pad_sequences(encoded, max_len=MAX_LEN)



MODEL_PATH = "football_transformer.pt"

from src.model.transformer import FootballTransformer

device = torch.device("cpu")

if os.path.exists(MODEL_PATH):
    print("Loading saved model...")
    model = FootballTransformer(vocab_size=len(vocab)).to(device)
    model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
    model.eval()
else:
    print("Training new model...")
    model = train_model(padded, vocab_size=len(vocab), epochs=5, lr=1e-3)


embeddings = extract_embeddings(model, padded)

player_embeddings = {}

for i, seq_players in enumerate(player_ids):
    emb = embeddings[i]

    counts = Counter(seq_players)
    for pid, count in counts.items():
        if pid not in player_embeddings:
            player_embeddings[pid] = []

        player_embeddings[pid].append(emb * (count / len(seq_players)))





# average per player (NO normalization yet)
for pid in player_embeddings:
    vec = torch.stack(player_embeddings[pid]).mean(dim=0)
    player_embeddings[pid] = vec

# =========================
# 🔥 GLOBAL VECTOR REMOVAL
# =========================
all_vecs = torch.stack(list(player_embeddings.values()))  # (num_players, D)
global_vec = all_vecs.mean(dim=0)

for pid in player_embeddings:
    player_embeddings[pid] = player_embeddings[pid] - global_vec

# =========================
# ✅ Normalize AFTER removal
# =========================
for pid in player_embeddings:
    player_embeddings[pid] = F.normalize(player_embeddings[pid], dim=0)




sample_vec = next(iter(player_embeddings.values()))

torch.save({
    "embeddings": player_embeddings,
    "vocab_size": len(vocab),
    "num_players": len(player_embeddings),
    "embedding_dim": sample_vec.shape[0]
}, "player_embeddings.pt")

print("Saved player embeddings")

  

print("Number of players:", len(player_embeddings))

print("Embeddings shape:", embeddings.shape)
# 8. Debug prints
print("\n--- DATASET INFO ---")
print("Number of sequences:", len(flat_sequences))
print("Vocab size:", len(vocab))
print("Max len used:", MAX_LEN)

print("\nExample sequence (tokens):", flat_sequences[0][:20])
print("Example sequence (encoded):", padded[0][:20])



# pick random player
sample_player = list(player_embeddings.keys())[0]

similar = find_similar_players(sample_player, player_embeddings, top_k=5)

print(f"\nTop similar players to {sample_player}:")
for pid, score in similar:
    print(f"Player {pid} → similarity: {score:.4f}")  