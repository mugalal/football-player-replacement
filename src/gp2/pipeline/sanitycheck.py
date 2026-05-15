import json
from collections import defaultdict

from src.gp2.paths import PLAYER_MATCH_DOCS_LEGACY_PATH

file_path = PLAYER_MATCH_DOCS_LEGACY_PATH

lengths = []
player_doc_counts = defaultdict(int)

with open(file_path, "r", encoding="utf-8") as f:
    for line in f:
        doc = json.loads(line)
        lengths.append(len(doc["tokens"]))
        player_doc_counts[doc["player_id"]] += 1

print(f"Total docs: {len(lengths)}")
print(f"Min length: {min(lengths)}")
print(f"Max length: {max(lengths)}")
print(f"Average length: {sum(lengths)/len(lengths):.2f}")

short  = sum(1 for l in lengths if l < 20)
normal = sum(1 for l in lengths if 20 <= l <= 300)
long   = sum(1 for l in lengths if l > 300)

print(f"\nToken distribution:")
print(f"Too short  (<20):    {short}")
print(f"Normal     (20–300): {normal}")
print(f"Too long   (>300):   {long}")

print(f"\nPlayer-level stats:")
print(f"Unique players: {len(player_doc_counts)}")
print(f"Players with <5 match docs:   {sum(1 for v in player_doc_counts.values() if v < 5)}")
print(f"Players with 5–30 match docs: {sum(1 for v in player_doc_counts.values() if 5 <= v <= 30)}")
print(f"Players with >30 match docs:  {sum(1 for v in player_doc_counts.values() if v > 30)}")
