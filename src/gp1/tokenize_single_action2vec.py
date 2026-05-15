"""
Single-token Action2Vec preprocessing
-------------------------------------

Exactly same pipeline structure as multi-token version BUT:

Event -> ONE fused token such as:

  pass_zone5_success
  pass_zone14_fail

  shot_zone12_right_foot
  shot_zone2_head

  carry_zone7
  pressure_zone3
  ball_receipt_zone10

Notes:
  • No artificial '_na' tokens are used
  • Outcomes are only included when StatsBomb defines them
  • Shot tokens include body part to match multi-token richness
"""

import json
import os
from collections import defaultdict

from data_processing import (
    load_all_events,
    xy_to_zone,
    NUM_X_BINS,
    NUM_Y_BINS
)

DATA_DIR = "data"

OUT_PLAY2VEC = "models/gp1/single_token/sentences_play2vec_single.jsonl"
OUT_ACTION2VEC = "models/gp1/single_token/sentences_action2vec_single.jsonl"


def event_to_single_token(ev):
    """
    Convert ONE StatsBomb event into ONE fused token
    """

    ev_type = ev.get("type", {}).get("name", "").lower()

    # field zone
    loc = ev.get("location", [None, None])
    zone = xy_to_zone(loc[0], loc[1], NUM_X_BINS, NUM_Y_BINS)

    # default token base
    base = f"{ev_type}_zone_{zone}"

    # -------- PASS --------
    if ev_type == "pass":
        p = ev.get("pass", {})
        # StatsBomb marks failure explicitly, success = lack of failure
        if p.get("outcome") is None:
            return f"{base}_success"
        else:
            return f"{base}_fail"

    # -------- SHOT --------
    elif ev_type == "shot":
        s = ev.get("shot", {})

        # body part (Right Foot, Head...)
        body = s.get("body_part", {}).get("name")
        if body:
            body = body.lower().replace(" ", "_")
            return f"{base}_{body}"

        # fallback if somehow body missing
        return base

    # -------- DRIBBLE --------
    elif ev_type == "dribble":
        d = ev.get("dribble", {})
        outcome = d.get("outcome", {}).get("name")

        if outcome:
            outcome = outcome.lower().replace(" ", "_")
            return f"{base}_{outcome}"

        return base

    # -------- OTHER EVENTS (carry, pressure, receipt, etc.) --------
    # They do NOT have explicit outcome in StatsBomb
    return base


def build_possession_sentences_single(events):
    """
    Aggregate tokens by (match, period, possession, team)
    """

    sentences = defaultdict(list)

    for ev in events:
        match_id = ev["match_id"]
        period = ev.get("period")
        possession = ev.get("possession")
        team = ev.get("possession_team", {}).get("id")

        key = (match_id, period, possession, team)

        token = event_to_single_token(ev)
        sentences[key].append(token)

    # keep possessions with >= 3 tokens
    return [
        (key, toks)
        for key, toks in sentences.items()
        if len(toks) >= 3
    ]


def save_jsonl(sentences, path, include_tokens_only=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        for key, toks in sentences:
            if include_tokens_only:
                f.write(json.dumps(toks) + "\n")
            else:
                f.write(json.dumps({
                    "play_id": list(key),
                    "tokens": toks
                }) + "\n")


def main():
    print("Loading events...")
    events = load_all_events(DATA_DIR)

    print("Building single-token possession sentences...")
    sentences = build_possession_sentences_single(events)

    print(f"Final possessions: {len(sentences)}")

    print("Saving...")
    save_jsonl(sentences, OUT_PLAY2VEC)
    save_jsonl(sentences, OUT_ACTION2VEC, include_tokens_only=True)

    print("Done.")


if __name__ == "__main__":
    main()
