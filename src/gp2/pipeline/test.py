from collections import Counter
from src.gp2.preprocess.tokens import event_to_tokens
from src.gp2.paths import TOP5_DATA_DIR
import json

with open(TOP5_DATA_DIR / "265839.json") as f:
    events = json.load(f)

type_lengths = Counter()
for ev in events:
    tokens = event_to_tokens(ev)
    event_type = ev.get("type", {}).get("name", "unknown")
    type_lengths[event_type] += len(tokens)

# See which event types are generating the most tokens
for event_type, total in type_lengths.most_common(15):
    print(f"{event_type}: {total} total tokens")
