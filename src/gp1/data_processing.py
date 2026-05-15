"""
StatsBomb → football2vec-style preprocessing (v1.0)
---------------------------------------------------

- Reads StatsBomb event JSON files from ./data/
- Converts each event into MULTIPLE tokens (Action2Vec idea)
- Groups events by (match_id, period, possession)
- Each possession becomes ONE sentence (Play2Vec idea)
- Saves sentences to models/sentences.jsonl

Author: Omar Sameh (GP prototype)
Reference: Ofir Magdaci – football2vec
"""

import json
import os
from collections import defaultdict, Counter

# =====================
# CONFIG
# =====================

DATA_DIR = "data"
OUT_ACTION2VEC = "models/gp1/multi_token/sentences_action2vec.jsonl"
OUT_PLAY2VEC   = "models/gp1/multi_token/sentences_play2vec.jsonl"


NUM_X_BINS = 6
NUM_Y_BINS = 3

PRUNE_THRESHOLD = 3          # keep tokens with freq >= threshold
PASS_SHORT_THRESHOLD = 20.0  # meters

VALID_EVENT_TYPES = {
    "pass",
    "carry",
    "dribble",
    "shot",
    "duel",
    "pressure",
    "ball receipt*",
    "interception",
    "clearance",
    "ball recovery",
    "miscontrol",
    "foul won",
    "foul committed"
}


# =====================
# HELPERS
# =====================

def xy_to_zone(x, y, num_x=NUM_X_BINS, num_y=NUM_Y_BINS):
    """
    Convert StatsBomb (x,y) to zone token.
    Pitch: x ∈ [0,120], y ∈ [0,80]
    """
    if x is None or y is None:
        return "zone_unknown"

    x = max(0.0, min(120.0, float(x)))
    y = max(0.0, min(80.0, float(y)))

    bx = min(int((x / 120.0) * num_x), num_x - 1)
    by = min(int((y / 80.0) * num_y), num_y - 1)

    return f"zone_{by * num_x + bx}"


def load_all_events(data_dir):
    """
    Load all StatsBomb event files and inject match_id from filename.
    """
    events = []

    for fname in sorted(os.listdir(data_dir)):
        if not fname.endswith(".json"):
            continue

        match_id = int(fname.replace(".json", ""))
        path = os.path.join(data_dir, fname)

        with open(path, "r", encoding="utf-8") as f:
            try:
                match_events = json.load(f)
                for ev in match_events:
                    ev["match_id"] = match_id
                    events.append(ev)
            except Exception as e:
                print(f"[WARN] Failed to read {fname}: {e}")

    return events


# =====================
# EVENT → TOKENS
# =====================

def event_to_tokens(ev):
    """
    Convert ONE StatsBomb event into MULTIPLE tokens.
    """
    tokens = []

    ev_type = ev.get("type", {}).get("name", "").lower()
    if ev_type not in VALID_EVENT_TYPES:
        return tokens
    loc = ev.get("location", [None, None])
    zone = xy_to_zone(loc[0], loc[1])

    # Base action tokens
    if ev_type:
        tokens.append(ev_type)
        tokens.append(f"{ev_type}_{zone}")

    # ---- PASS ----
    if ev_type == "pass":
        p = ev.get("pass", {})

        length = p.get("length")
        height = p.get("height", {}).get("name", "").lower()
        outcome = p.get("outcome")

        if length is not None:
            if length <= PASS_SHORT_THRESHOLD:
                tokens.append("pass_short")
            else:
                tokens.append("pass_long")

        if height:
            tokens.append(f"pass_height_{height}")

        if outcome is None:
            tokens.append("pass_success")
        else:
            tokens.append("pass_fail")

    # ---- SHOT ----
    if ev_type == "shot":
        s = ev.get("shot", {})
        body = s.get("body_part", {}).get("name", "").lower()
        outcome = s.get("outcome", {}).get("name", "").lower()

        if body:
            tokens.append(f"shot_body_{body}")
        if outcome:
            tokens.append(f"shot_outcome_{outcome}")

    return tokens


# =====================
# BUILD SENTENCES
# =====================

def build_possession_sentences(events):
    """
    Group events into possession-level sentences.
    Key = (match_id, period, possession, possession_team_id)
    """
    sentences = defaultdict(list)

    for ev in events:
        match_id = ev.get("match_id")
        period = ev.get("period")
        possession = ev.get("possession")
        possession_team = ev.get("possession_team", {}).get("id")

        if (
            match_id is None
            or period is None
            or possession is None
            or possession_team is None
        ):
            continue

        key = (match_id, period, possession, possession_team)
        tokens = event_to_tokens(ev)

        if tokens:
            sentences[key].extend(tokens)

    # Remove very short possessions
    return [
        (key, tokens)
        for key, tokens in sentences.items()
        if len(tokens) >= 3
    ]



# =====================
# PRUNING
# =====================

def prune_sentences(sentences, threshold=PRUNE_THRESHOLD):
    """
    sentences: [ (play_id, [tokens]) ]
    """
    counter = Counter()

    # Count token frequencies
    for _, tokens in sentences:
        counter.update(tokens)

    pruned = []
    for play_id, tokens in sentences:
        filtered = [t for t in tokens if counter[t] > threshold]
        if len(filtered) >= 3:
            pruned.append((play_id, filtered))

    return pruned, counter



# =====================
# SAVE
# =====================

def save_action2vec_sentences(sentences, out_path):
    """
    Saves ONLY token lists (used for Action2Vec training)
    Format:
        ["pass", "pass_zone_3", ...]
    """
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for _, tokens in sentences:
            f.write(json.dumps(tokens) + "\n")


def save_play2vec_sentences(sentences, out_path):
    """
    Saves play_id + tokens (used for Play2Vec)
    Format:
        {
          "play_id": [match_id, period, possession, possession_team_id],
          "tokens": [...]
        }
    """
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for play_id, tokens in sentences:
            record = {
                "play_id": list(play_id),
                "tokens": tokens
            }
            f.write(json.dumps(record) + "\n")
            


# =====================
# MAIN
# =====================

def main():
    print("Loading events...")
    events = load_all_events(DATA_DIR)
    print(f"Loaded {len(events):,} events")

    print("\nBuilding possession-level sentences...")
    sentences = build_possession_sentences(events)
    print(f"Built {len(sentences):,} possession sentences")

    print("\nPruning rare tokens...")
    sentences, vocab = prune_sentences(sentences)

    print(f"Final sentences: {len(sentences):,}")
    print(f"Vocabulary size: {len(vocab):,}")

    # =====================
    # SANITY CHECKS
    # =====================
    lengths = [len(s) for s in sentences]
    print("\nPossession length stats:")
    print(f"  Min  : {min(lengths)}")
    print(f"  Mean : {sum(lengths)/len(lengths):.2f}")
    print(f"  Max  : {max(lengths)}")

    print("\nTop 20 most frequent tokens:")
    for tok, cnt in vocab.most_common(20):
        print(f"  {tok:<25} {cnt}")

    print("\nSaving sentences...")
    save_action2vec_sentences(sentences, OUT_ACTION2VEC)
    print(f"Saved to {OUT_ACTION2VEC}")

    print("Saving Play2Vec sentences...")
    save_play2vec_sentences(sentences, OUT_PLAY2VEC)
    print(f"Saved to {OUT_PLAY2VEC}")
    


if __name__ == "__main__":
    main()
