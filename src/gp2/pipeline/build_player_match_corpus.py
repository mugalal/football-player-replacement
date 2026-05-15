"""
Build Player-Match Corpus with Separate On-Ball and Off-Ball Documents — V2

V2 Changes:
    - Uses updated tokens.py (V2) with semantic markers (cut_inside, to_box, key_pass, etc.)
    - Single document per player-match (no position segmentation)
      Following Magdaci's proven approach — position info will be tracked separately
      for downstream filtering/analysis, not encoded in document boundaries.
    - GKs handled with empty offball lists (zero-padded later in build_player2vec)
    - Token budgets unchanged (proven to balance event types correctly)

Output format per line (JSONL):
{
    "player_id": "5246",
    "match_id": "265839",
    "primary_position": "Center Forward",   # most-frequent position in this match
    "position_distribution": {              # for versatility analysis later
        "Center Forward": 45,
        "Left Wing": 12
    },
    "onball_tokens": [...],                 # on-ball actions (passes, carries, shots, dribbles)
    "offball_tokens": [...]                 # defensive/pressing actions (can be empty for GKs)
}
"""

import json
import random
from collections import defaultdict, Counter
from pathlib import Path

from src.gp2.preprocess.tokens import event_to_tokens
from src.gp2.paths import PLAYER_MATCH_DOCS_PATH, TOP5_DATA_DIR


# ==================================================================================================
# EVENT CLASSIFICATION (unchanged from V1)
# ==================================================================================================

ONBALL_EVENTS = {
    "Pass",
    "Carry",
    "Dribble",
    "Shot",
    "Foul Committed",
    "Ball Recovery",
}

OFFBALL_EVENTS = {
    "Pressure",
    "Block",
    "Dribbled Past",
    "Dispossessed",
    "Clearance",
    "Interception",
    "Duel",
}


# ==================================================================================================
# TOKEN BUDGETING (unchanged — proven to work)
# ==================================================================================================

ONBALL_BUDGET = {
    "Pass":           80,
    "Carry":          50,
    "Shot":           30,
    "Dribble":        25,
    "Ball Recovery":  20,
    "Foul Committed": 15,
}

OFFBALL_BUDGET = {
    "Pressure":       50,
    "Duel":           30,
    "Clearance":      25,
    "Interception":   25,
    "Block":          20,
    "Dribbled Past":  15,
    "Dispossessed":   15,
}


def build_balanced_doc(tokens_by_type, event_set, budget_map):
    """
    Build balanced document from tokens grouped by event type.
    Caps each event type at its budget to prevent dominant types
    (e.g., Pass) from drowning out distinctive ones (e.g., Shot).
    """
    doc = []

    for event_type, tokens in tokens_by_type.items():
        if event_type not in event_set:
            continue

        budget = budget_map.get(event_type, 20)
        doc.extend(tokens[:budget])

    random.shuffle(doc)
    return doc


# ==================================================================================================
# MATCH PROCESSING
# ==================================================================================================

def process_match(file_path):
    """
    Process one match. Returns: dict {player_id: doc_dict, ...}, match_id

    For each player in the match:
      - Collect tokens by event type
      - Track which positions they played (for metadata)
      - Build separate onball + offball documents
    """
    with open(file_path, "r", encoding="utf-8") as f:
        events = json.load(f)

    match_id = Path(file_path).stem

    # Per player: tokens grouped by event type, position counter
    player_type_tokens = defaultdict(lambda: defaultdict(list))
    player_position_counts = defaultdict(Counter)

    for event in events:
        # Skip events without a player (e.g., team-level events)
        if "player" not in event or event["player"] is None:
            continue

        player_id = event["player"]["id"]
        event_type = event.get("type", {}).get("name", "unknown")

        # Track position (from event metadata)
        position = event.get("position", {}).get("name") if event.get("position") else None
        if position:
            player_position_counts[player_id][position] += 1

        # Tokenize and collect
        tokens = event_to_tokens(event)
        if len(tokens) >= 1:
            player_type_tokens[player_id][event_type].extend(tokens)

    # Build documents per player
    player_docs = {}

    for player_id, type_tokens in player_type_tokens.items():
        onball = build_balanced_doc(type_tokens, ONBALL_EVENTS, ONBALL_BUDGET)
        offball = build_balanced_doc(type_tokens, OFFBALL_EVENTS, OFFBALL_BUDGET)

        # Require minimum on-ball tokens (off-ball can be empty for GKs)
        if len(onball) < 10:
            continue

        # Determine primary position (most events) and full distribution
        position_dist = dict(player_position_counts[player_id])
        primary_position = (
            max(position_dist, key=position_dist.get) if position_dist else "Unknown"
        )

        player_docs[player_id] = {
            "onball": onball,
            "offball": offball,
            "primary_position": primary_position,
            "position_distribution": position_dist,
        }

    return player_docs, match_id


# ==================================================================================================
# MAIN
# ==================================================================================================

def main():
    PLAYER_MATCH_DOCS_PATH.parent.mkdir(parents=True, exist_ok=True)

    total_docs = 0
    total_onball_tokens = 0
    total_offball_tokens = 0
    docs_with_no_offball = 0
    position_distribution = Counter()

    print("Building player-match corpus (V2)...")
    print(f"Reading from: {TOP5_DATA_DIR}")
    print(f"Writing to:   {PLAYER_MATCH_DOCS_PATH}\n")

    with open(PLAYER_MATCH_DOCS_PATH, "w", encoding="utf-8") as out_file:
        match_files = list(TOP5_DATA_DIR.glob("*.json"))
        total_matches = len(match_files)

        for i, file in enumerate(match_files):
            player_docs, match_id = process_match(file)

            for player_id, docs in player_docs.items():
                doc = {
                    "player_id": str(player_id),
                    "match_id": match_id,
                    "primary_position": docs["primary_position"],
                    "position_distribution": docs["position_distribution"],
                    "onball_tokens": docs["onball"],
                    "offball_tokens": docs["offball"],
                }
                json.dump(doc, out_file)
                out_file.write("\n")

                total_docs += 1
                total_onball_tokens += len(docs["onball"])
                total_offball_tokens += len(docs["offball"])

                if len(docs["offball"]) == 0:
                    docs_with_no_offball += 1

                position_distribution[docs["primary_position"]] += 1

            if i % 50 == 0:
                print(f"Processed {i}/{total_matches} matches | docs: {total_docs}")

    print("\n" + "=" * 60)
    print("CORPUS BUILD COMPLETE")
    print("=" * 60)
    print(f"Total player-match documents: {total_docs}")
    print(f"Total on-ball tokens:  {total_onball_tokens:,}")
    print(f"Total off-ball tokens: {total_offball_tokens:,}")
    print(f"Avg on-ball per doc:   {total_onball_tokens/total_docs:.1f}")
    print(f"Avg off-ball per doc:  {total_offball_tokens/total_docs:.1f}")
    print(f"Docs with NO off-ball: {docs_with_no_offball} (likely GKs/subs)")

    print(f"\nPosition distribution (top 15):")
    for pos, count in position_distribution.most_common(15):
        print(f"  {pos:<35} {count}")


if __name__ == "__main__":
    main()
