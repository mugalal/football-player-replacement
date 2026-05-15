import json
from src.preprocess.tokens import event_to_tokens
from src.preprocess.sequence_builder import build_possession_sequences

with open("data/laliga1516/265839.json", "r", encoding="utf-8") as f:
    events = json.load(f)

sequences = build_possession_sequences(events, event_to_tokens)

print("Total sequences:", len(sequences))

# print first 3 sequences
for i, seq in enumerate(sequences[:3]):
    print(f"\nSequence {i+1}:")
    for event_tokens in seq:
        print(event_tokens)