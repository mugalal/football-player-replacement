"""
Build 64D Player2Vec from Asymmetric On-Ball + Off-Ball Vectors — V2

V2 Architecture:
    - On-ball vectors:  48D (rich on-ball signal)
    - Off-ball vectors: 16D (sparser off-ball signal)
    - Concatenated:     64D
    - GKs zero-padded with 16D zeros for off-ball component

Pipeline:
    1. Load both Doc2Vec models (onball 48D + offball 16D)
    2. For each player:
        - Average match-level on-ball vectors  → 48D player on-ball
        - Average match-level off-ball vectors → 16D player off-ball
        - Concatenate → 64D raw player vector
    3. Aggregate position metadata (primary position, distribution, versatility)
    4. Remove dominant direction (PCA, n_components=1)
    5. Normalize → final 64D Player2Vec

Outputs:
    - models/gp2/player2vec_64d.npz       (player_ids + 64D vectors)
    - models/gp2/player_metadata_v2.json  (name, team, position info, versatility)
"""

import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from gensim.models.doc2vec import Doc2Vec

from src.gp2.paths import (
    OFFBALL_MODEL_PATH,
    ONBALL_MODEL_PATH,
    PLAYER2VEC_PATH,
    PLAYER_INFO_PATH,
    PLAYER_MATCH_DOCS_PATH,
    PLAYER_METADATA_PATH,
)


# ==================================================================================================
# DIMENSIONS
# ==================================================================================================

ONBALL_DIM = 48
OFFBALL_DIM = 16
TOTAL_DIM = ONBALL_DIM + OFFBALL_DIM  # 64

MIN_MATCHES = 5  # minimum matches required to include player


# ==================================================================================================
# DOMINANT VECTOR REMOVAL (unchanged from V1 — proven technique)
# ==================================================================================================

def remove_dominant_direction(vectors, n_components=1):
    """
    Remove top-N principal components (Mu et al. 2018, "All-but-the-Top").
    Critical for spreading similarity scores from compressed range.
    """
    mean_vec = vectors.mean(axis=0, keepdims=True)
    centered = vectors - mean_vec

    _, _, Vt = np.linalg.svd(centered, full_matrices=False)
    top_components = Vt[:n_components]

    for component in top_components:
        projection = (centered @ component).reshape(-1, 1) * component.reshape(1, -1)
        centered = centered - projection

    norms = np.linalg.norm(centered, axis=1, keepdims=True)
    norms = np.clip(norms, 1e-8, None)
    normalized = centered / norms

    return normalized


# ==================================================================================================
# POSITION METADATA AGGREGATION
# ==================================================================================================

def aggregate_position_metadata(docs_path):
    """
    Read corpus and aggregate per-player position info across all matches.
    Returns dict: player_id → {
        primary_position: str,
        position_distribution: {position: total_event_count},
        versatility_score: float (Shannon entropy),
        num_matches: int,
        num_distinct_positions: int  # positions with >=15 events total
    }
    """
    player_positions = defaultdict(Counter)  # player_id → {position: total events}
    player_match_count = Counter()           # player_id → number of matches

    with open(docs_path, "r", encoding="utf-8") as f:
        for line in f:
            doc = json.loads(line.strip())
            pid = doc["player_id"]
            player_match_count[pid] += 1

            # Sum event counts across matches
            for pos, count in doc.get("position_distribution", {}).items():
                player_positions[pid][pos] += count

    # Compute aggregate metadata per player
    metadata = {}
    for pid, position_counts in player_positions.items():
        total_events = sum(position_counts.values())
        if total_events == 0:
            continue

        # Primary position = most events
        primary_position = position_counts.most_common(1)[0][0]

        # Versatility via Shannon entropy
        # 0 = single position, higher = more spread across positions
        entropy = 0.0
        for count in position_counts.values():
            p = count / total_events
            if p > 0:
                entropy -= p * math.log(p)

        # Distinct positions (with at least 15 events total — meaningful playtime)
        distinct = sum(1 for count in position_counts.values() if count >= 15)

        metadata[pid] = {
            "primary_position": primary_position,
            "position_distribution": dict(position_counts),
            "versatility_score": round(entropy, 4),
            "num_distinct_positions": distinct,
            "num_matches": player_match_count[pid],
        }

    return metadata


# ==================================================================================================
# BUILD 64D PLAYER2VEC
# ==================================================================================================

def build_player2vec(min_matches=MIN_MATCHES, n_components=1):
    """Aggregate match vectors into player vectors and clean."""

    # ---------------- LOAD MODELS ----------------
    print("Loading Doc2Vec models...")
    onball_model = Doc2Vec.load(str(ONBALL_MODEL_PATH))
    offball_model = Doc2Vec.load(str(OFFBALL_MODEL_PATH))

    # Sanity check dimensions
    actual_onball_dim = onball_model.dv[onball_model.dv.index_to_key[0]].shape[0]
    actual_offball_dim = offball_model.dv[offball_model.dv.index_to_key[0]].shape[0]

    print(f"  On-ball model:  {len(onball_model.dv):,} doc vectors, dim={actual_onball_dim}")
    print(f"  Off-ball model: {len(offball_model.dv):,} doc vectors, dim={actual_offball_dim}")

    if actual_onball_dim != ONBALL_DIM or actual_offball_dim != OFFBALL_DIM:
        raise ValueError(
            f"Dimension mismatch! Expected {ONBALL_DIM}+{OFFBALL_DIM}, "
            f"got {actual_onball_dim}+{actual_offball_dim}. "
            f"Did train_playermatch2vec.py run with the right dimensions?"
        )

    # ---------------- GROUP MATCH VECTORS BY PLAYER ----------------
    print("\nGrouping match vectors by player...")
    player_onball = defaultdict(list)
    player_offball = defaultdict(list)

    for doc_tag in onball_model.dv.index_to_key:
        player_id = doc_tag.split("_")[0]
        player_onball[player_id].append(onball_model.dv[doc_tag])

    for doc_tag in offball_model.dv.index_to_key:
        player_id = doc_tag.split("_")[0]
        player_offball[player_id].append(offball_model.dv[doc_tag])

    print(f"  Players with on-ball data:  {len(player_onball):,}")
    print(f"  Players with off-ball data: {len(player_offball):,}")

    # ---------------- LOAD POSITION METADATA ----------------
    print("\nAggregating position metadata across matches...")
    position_metadata = aggregate_position_metadata(PLAYER_MATCH_DOCS_PATH)
    print(f"  Players with position metadata: {len(position_metadata):,}")

    # ---------------- LOAD EXISTING PLAYER INFO (name, team) ----------------
    if Path(PLAYER_INFO_PATH).exists():
        with open(PLAYER_INFO_PATH, "r", encoding="utf-8") as f:
            player_info = json.load(f)
        print(f"  Loaded existing player_info: {len(player_info):,} players")
    else:
        print(f"  ⚠ {PLAYER_INFO_PATH} not found — name/team will be missing")
        player_info = {}

    # ---------------- BUILD 64D VECTORS ----------------
    valid_ids = []
    raw_vectors = []
    excluded_too_few = 0
    gk_zero_padded = 0

    for player_id in player_onball.keys():
        onball_vecs = player_onball[player_id]

        if len(onball_vecs) < min_matches:
            excluded_too_few += 1
            continue

        mean_onball = np.mean(onball_vecs, axis=0)  # 48D

        # Handle missing off-ball (goalkeepers, mostly)
        if player_id not in player_offball:
            mean_offball = np.zeros(OFFBALL_DIM)
            gk_zero_padded += 1
        else:
            offball_vecs = player_offball[player_id]
            if len(offball_vecs) < min_matches:
                # Has off-ball but too few matches — still zero-pad rather than exclude
                mean_offball = np.zeros(OFFBALL_DIM)
                gk_zero_padded += 1
            else:
                mean_offball = np.mean(offball_vecs, axis=0)  # 16D

        combined = np.concatenate([mean_onball, mean_offball])  # 64D
        valid_ids.append(player_id)
        raw_vectors.append(combined)

    raw_vectors = np.array(raw_vectors)

    print(f"\nPlayers in final Player2Vec: {len(valid_ids):,}")
    print(f"  Zero-padded off-ball (GKs/few matches): {gk_zero_padded}")
    print(f"  Excluded (too few on-ball matches):     {excluded_too_few}")
    print(f"  Vector shape: {raw_vectors.shape}")

    # ---------------- DOMINANT VECTOR REMOVAL ----------------
    print(f"\nRemoving {n_components} dominant component(s)...")

    # Stats before
    norms_before = np.linalg.norm(raw_vectors, axis=1, keepdims=True)
    normalized_before = raw_vectors / np.clip(norms_before, 1e-8, None)
    sims_before = normalized_before @ normalized_before.T
    np.fill_diagonal(sims_before, 0)

    print(f"\nBefore removal:")
    print(f"  Mean similarity:  {sims_before.mean():.4f}")
    print(f"  Min similarity:   {sims_before.min():.4f}")
    print(f"  Max similarity:   {sims_before.max():.4f}")

    cleaned_vectors = remove_dominant_direction(raw_vectors, n_components)

    # Stats after
    sims_after = cleaned_vectors @ cleaned_vectors.T
    np.fill_diagonal(sims_after, 0)

    print(f"\nAfter removal:")
    print(f"  Mean similarity:  {sims_after.mean():.4f}")
    print(f"  Min similarity:   {sims_after.min():.4f}")
    print(f"  Max similarity:   {sims_after.max():.4f}")

    # ---------------- SAVE PLAYER2VEC ----------------
    player_ids_array = np.array(valid_ids)
    np.savez(
        PLAYER2VEC_PATH,
        player_ids=player_ids_array,
        vectors=cleaned_vectors,
    )
    print(f"\n✓ Player2Vec ({TOTAL_DIM}D) saved: {PLAYER2VEC_PATH}")
    print(f"  Shape: {cleaned_vectors.shape}")

    # ---------------- SAVE ENRICHED METADATA ----------------
    print(f"\nBuilding enriched metadata...")
    enriched_metadata = {}
    for pid in valid_ids:
        info = player_info.get(pid, {})
        pos_meta = position_metadata.get(pid, {})

        enriched_metadata[pid] = {
            "name": info.get("name", "Unknown"),
            "team": info.get("team", "Unknown"),
            "primary_position": pos_meta.get("primary_position", info.get("position", "Unknown")),
            "position_distribution": pos_meta.get("position_distribution", {}),
            "versatility_score": pos_meta.get("versatility_score", 0.0),
            "num_distinct_positions": pos_meta.get("num_distinct_positions", 1),
            "num_matches": pos_meta.get("num_matches", 0),
        }

    with open(PLAYER_METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(enriched_metadata, f, ensure_ascii=False, indent=2)
    print(f"✓ Enriched metadata saved: {PLAYER_METADATA_PATH}")

    # ---------------- SANITY CHECKS ----------------
    print("\n" + "=" * 80)
    print("SANITY CHECK — Top 5 similar players for sample players")
    print("=" * 80)

    sample_names = ["Suárez", "Neymar", "Mané", "Messi", "Iniesta"]
    name_to_idx = {}
    for i, pid in enumerate(valid_ids):
        name = enriched_metadata[pid]["name"]
        for sample in sample_names:
            if sample in name:
                name_to_idx[sample] = i
                break

    for sample, idx in name_to_idx.items():
        target_vec = cleaned_vectors[idx]
        sims = cleaned_vectors @ target_vec
        sims[idx] = -1  # exclude self

        top_indices = np.argsort(sims)[::-1][:5]

        target_meta = enriched_metadata[valid_ids[idx]]
        print(
            f"\n{target_meta['name']} ({target_meta['primary_position']}, "
            f"{target_meta['team']}, versatility={target_meta['versatility_score']}):"
        )
        for i in top_indices:
            sim_meta = enriched_metadata[valid_ids[i]]
            print(
                f"  {sim_meta['name']:<35} "
                f"({sim_meta['primary_position']:<25}, {sim_meta['team']:<22}) "
                f"→ {sims[i]:.4f}"
            )

    # ---------------- VERSATILITY HIGHLIGHTS ----------------
    print("\n" + "=" * 80)
    print("VERSATILITY HIGHLIGHTS — Most versatile players (entropy + distinct positions)")
    print("=" * 80)

    versatile_players = sorted(
        enriched_metadata.items(),
        key=lambda kv: (kv[1]["num_distinct_positions"], kv[1]["versatility_score"]),
        reverse=True,
    )[:15]

    print(f"\n{'Player':<35} {'Primary Pos':<25} {'Distinct':<10} {'Entropy':<10}")
    print("-" * 90)
    for pid, meta in versatile_players:
        print(
            f"{meta['name']:<35} {meta['primary_position']:<25} "
            f"{meta['num_distinct_positions']:<10} {meta['versatility_score']:<10.4f}"
        )


# ==================================================================================================
# MAIN
# ==================================================================================================

def main():
    print("=" * 80)
    print(f"BUILDING {TOTAL_DIM}D PLAYER2VEC (V2)")
    print(f"  On-ball:  {ONBALL_DIM}D  +  Off-ball: {OFFBALL_DIM}D")
    print("=" * 80)
    build_player2vec(min_matches=MIN_MATCHES, n_components=1)


if __name__ == "__main__":
    main()
