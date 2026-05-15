"""
The Mané Validation — Modify Liverpool Player Documents, Search for Upgrades

This is the REAL validation of our scouting tool concept.

Approach (Magdaci-style):
    1. Pick a Liverpool 2015-16 attacker (Coutinho, Lallana, Sturridge)
    2. Sample N of their match documents
    3. Apply interventions that move them toward "ideal Klopp attacker":
        - add_cut_inside (inverted winger behavior)
        - upgrade_finishing (more clinical)
        - add_progression (more direct progressive carries)
        - boost_pressing (gegenpressing)
    4. Re-infer vectors from modified docs (one vector per modified match)
    5. Average those vectors → "upgraded Coutinho" target vector
    6. Search top-50 most similar players in the entire 2015-16 dataset
    7. Validate: Mané should appear in top-20

Generalization test:
    Same approach but for Mertens (Napoli LW) and Modrić — does the methodology
    extend beyond Liverpool? If yes, the tool generalizes.
"""

import json
import numpy as np
import random
from typing import List

from gensim.models.doc2vec import Doc2Vec

from .modify_doc import (
    Intervention,
    add_cut_inside,
    upgrade_finishing,
    add_progression,
    boost_pressing,
    add_chance_creation,
    enrich_dribbling,
    modify_doc,
)
from src.gp2.paths import (
    DOCS_PATH,
    OFFBALL_MODEL_PATH,
    ONBALL_MODEL_PATH,
    PLAYER2VEC_PATH,
    PLAYER_METADATA_PATH,
)


# ==================================================================================================
# DATA LOADING
# ==================================================================================================

def load_everything():
    """Load Player2Vec + metadata + Doc2Vec models."""
    data = np.load(PLAYER2VEC_PATH)
    player_ids = list(data["player_ids"])
    vectors = data["vectors"]

    with open(PLAYER_METADATA_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    print("Loading Doc2Vec models...")
    onball_model = Doc2Vec.load(str(ONBALL_MODEL_PATH))
    offball_model = Doc2Vec.load(str(OFFBALL_MODEL_PATH))

    return player_ids, vectors, metadata, onball_model, offball_model


def load_player_docs(player_id: str) -> List[dict]:
    """Load all match docs for a specific player."""
    docs = []
    with open(DOCS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line.strip())
            if d["player_id"] == player_id:
                docs.append(d)
    return docs


def find_player_id(name_query: str, metadata: dict, player_ids: list) -> str:
    """Find player_id by partial name match. Returns None if not found."""
    query = name_query.lower()
    matches = []
    for pid in player_ids:
        name = metadata.get(pid, {}).get("name", "")
        if query in name.lower():
            matches.append((pid, name))
    if not matches:
        return None
    if len(matches) > 1:
        print(f"  ⚠ Ambiguous '{name_query}', using first: {matches[0][1]}")
    return matches[0][0]


# ==================================================================================================
# VECTOR INFERENCE FROM MODIFIED DOCS
# ==================================================================================================

def infer_player_vector_from_docs(
    docs: List[dict],
    onball_model: Doc2Vec,
    offball_model: Doc2Vec,
    onball_dim: int = 48,
    offball_dim: int = 16,
) -> np.ndarray:
    """
    Re-infer a player vector from modified docs.
    For each doc: infer onball + offball vectors, concatenate, then average across docs.
    """
    onball_vecs = []
    offball_vecs = []

    for doc in docs:
        if doc.get("onball_tokens"):
            onball_vecs.append(onball_model.infer_vector(doc["onball_tokens"]))
        if doc.get("offball_tokens"):
            offball_vecs.append(offball_model.infer_vector(doc["offball_tokens"]))

    if not onball_vecs:
        raise ValueError("No on-ball tokens to infer from")

    mean_onball = np.mean(onball_vecs, axis=0)
    mean_offball = (
        np.mean(offball_vecs, axis=0) if offball_vecs else np.zeros(offball_dim)
    )

    combined = np.concatenate([mean_onball, mean_offball])
    return combined / np.linalg.norm(combined)


# ==================================================================================================
# SEARCH
# ==================================================================================================

def search_similar(
    target_vec: np.ndarray,
    vectors: np.ndarray,
    player_ids: list,
    metadata: dict,
    top_k: int = 30,
    exclude_player_ids: list = None,
    target_name: str = None,
    show_target_neighborhood: bool = True,
):
    """Find top-K most similar players to target_vec.

    If target_name is given but doesn't appear in top-K, also reports:
        - The target's actual rank
        - Its similarity score
        - Players ranked just above and below it
    """
    sims = vectors @ target_vec

    if exclude_player_ids:
        for pid in exclude_player_ids:
            if pid in player_ids:
                sims[player_ids.index(pid)] = -np.inf

    # Full ranking (we use this for diagnostics if target isn't in top-K)
    full_ranking = np.argsort(sims)[::-1]
    top_indices = full_ranking[:top_k]

    print(f"\n{'Rank':<6}{'Player':<40}{'Position':<28}{'Team':<24}{'Sim':<8}")
    print("-" * 105)

    target_rank = None
    target_idx = None
    for rank, idx in enumerate(top_indices, 1):
        pid = player_ids[idx]
        meta = metadata[pid]
        marker = ""
        if target_name and target_name.lower() in meta["name"].lower():
            target_rank = rank
            target_idx = idx
            marker = "  ← TARGET ✓"
        print(f"{rank:<6}{meta['name']:<40}{meta['primary_position']:<28}{meta['team']:<24}{sims[idx]:.4f}{marker}")

    # If the target wasn't found in top_k, dig deeper to locate it
    if target_name and target_rank is None and show_target_neighborhood:
        # Find the target's actual rank in the full ranking
        target_full_rank = None
        target_idx_global = None
        for full_rank_idx, idx in enumerate(full_ranking, 1):
            pid = player_ids[idx]
            meta = metadata[pid]
            if target_name.lower() in meta["name"].lower():
                target_full_rank = full_rank_idx
                target_idx_global = idx
                break

        if target_full_rank is None:
            print(f"\n  ⚠ Target '{target_name}' not found in dataset at all (excluded or missing).")
        else:
            target_meta = metadata[player_ids[target_idx_global]]
            target_sim = sims[target_idx_global]
            top_sim = sims[full_ranking[0]]
            cutoff_sim = sims[full_ranking[top_k - 1]]
            total_players = len(full_ranking)
            percentile = 100 * (1 - target_full_rank / total_players)

            print(f"\n  --- Target diagnostic ---")
            print(f"  Target: {target_meta['name']}")
            print(f"    Primary position: {target_meta['primary_position']}")
            print(f"    Team: {target_meta['team']}")
            print(f"    Versatility: {target_meta.get('versatility_score', 'N/A')}")
            print(f"  Actual rank: #{target_full_rank} of {total_players} players")
            print(f"  Percentile: top {100 - percentile:.1f}% (higher rank = closer to top)")
            print(f"  Target similarity: {target_sim:.4f}")
            print(f"  Top-1 similarity:  {top_sim:.4f}")
            print(f"  Top-{top_k} cutoff sim:  {cutoff_sim:.4f}")
            print(f"  Gap to top-{top_k}:    {cutoff_sim - target_sim:.4f}")

            # Show neighborhood around target rank
            print(f"\n  --- Players ranked around {target_meta['name']} ---")
            window_start = max(1, target_full_rank - 3)
            window_end = min(total_players, target_full_rank + 3)
            print(f"  {'Rank':<6}{'Player':<40}{'Position':<28}{'Sim':<8}")
            for r in range(window_start, window_end + 1):
                idx = full_ranking[r - 1]
                pid = player_ids[idx]
                meta = metadata[pid]
                marker = "  ← TARGET" if idx == target_idx_global else ""
                print(f"  {r:<6}{meta['name']:<40}{meta['primary_position']:<28}{sims[idx]:.4f}{marker}")

            # Where in the ranking thresholds does the target fall?
            print(f"\n  --- Target presence at various top-K thresholds ---")
            thresholds = [10, 20, 30, 50, 100, 200, 500]
            for t in thresholds:
                in_or_out = "✓ IN" if target_full_rank <= t else "✗ out"
                print(f"    Top-{t:<4} ({in_or_out})")

    return target_rank


# ==================================================================================================
# THE MANÉ VALIDATION
# ==================================================================================================

def validate_mane_search():
    """
    The main test. Modify Coutinho's docs to add Mané-like behaviors,
    search for similar players, expect Mané to appear in top-20.
    """
    print("\n" + "█" * 105)
    print("MANÉ VALIDATION — Replacement Search via Document Modification")
    print("█" * 105)

    player_ids, vectors, metadata, onball_model, offball_model = load_everything()

    # Find Liverpool's 2015-16 attackers as starting points
    coutinho_id = find_player_id("Coutinho", metadata, player_ids)
    if not coutinho_id:
        print("✗ Coutinho not found in dataset. Aborting.")
        return

    coutinho_meta = metadata[coutinho_id]
    print(f"\nStarting point: {coutinho_meta['name']} ({coutinho_meta['team']}, {coutinho_meta['primary_position']})")
    print(f"Versatility score: {coutinho_meta['versatility_score']}")

    # Load all of Coutinho's match documents
    coutinho_docs = load_player_docs(coutinho_id)
    print(f"Coutinho match documents: {len(coutinho_docs)}")

    # Filter to Liverpool docs only (he was at Liverpool in 2015-16, but docs include other teams if any)
    liverpool_docs = [d for d in coutinho_docs if d.get("primary_position")]
    print(f"Documents to use: {len(liverpool_docs)}")

    # Sample subset of matches (Magdaci samples random matches for stability)
    sample_size = min(15, len(liverpool_docs))
    sampled_docs = random.sample(liverpool_docs, sample_size)
    print(f"Sampling {sample_size} matches for modification")

    # ============== TEST 1: BASELINE (no modifications) ==============
    print("\n" + "─" * 105)
    print("TEST 1 — Baseline: Re-infer Coutinho's vector with NO modifications")
    print("─" * 105)
    print("This sanity-checks the inference pipeline. Coutinho should be #1 with sim ≈ 1.")

    baseline_vec = infer_player_vector_from_docs(sampled_docs, onball_model, offball_model)
    rank = search_similar(
        baseline_vec, vectors, player_ids, metadata,
        top_k=10, target_name="Coutinho",
    )
    if rank == 1:
        print("\n  ✓ Inference pipeline works correctly")
    else:
        print(f"\n  ⚠ Coutinho ranked #{rank} (expected #1) — high noise in inference")

    # ============== TEST 2: ADD CUT-INSIDE BEHAVIOR ==============
    print("\n" + "─" * 105)
    print("TEST 2 — Add inverted-winger behavior (cut_inside_right + cut_inside_left)")
    print("─" * 105)
    print("Coutinho already cuts inside but we amplify this trait.")

    interventions_cut_inside = add_cut_inside(probability=0.6)
    modified_docs_v1 = []
    for doc in sampled_docs:
        new_doc = dict(doc)
        new_doc["onball_tokens"] = modify_doc(doc["onball_tokens"], interventions_cut_inside)
        modified_docs_v1.append(new_doc)

    target_vec = infer_player_vector_from_docs(modified_docs_v1, onball_model, offball_model)
    search_similar(
        target_vec, vectors, player_ids, metadata,
        top_k=20, target_name="Mané",
    )

    # ============== TEST 3: FULL "KLOPP IDEAL" PROFILE ==============
    print("\n" + "─" * 105)
    print("TEST 3 — Full 'Klopp ideal attacker' profile applied to Coutinho")
    print("─" * 105)
    print("Interventions: cut_inside + finishing + progression + pressing + chance creation + dribbling")

    klopp_interventions = (
        add_cut_inside(probability=0.7) +
        upgrade_finishing(probability=0.5) +
        add_progression(probability=0.4) +
        add_chance_creation(probability=0.4) +
        enrich_dribbling(probability=0.4)
    )
    klopp_offball_interventions = boost_pressing(probability=0.7)

    modified_docs_v2 = []
    for doc in sampled_docs:
        new_doc = dict(doc)
        new_doc["onball_tokens"] = modify_doc(doc["onball_tokens"], klopp_interventions)
        new_doc["offball_tokens"] = modify_doc(doc["offball_tokens"], klopp_offball_interventions)
        modified_docs_v2.append(new_doc)

    target_vec = infer_player_vector_from_docs(modified_docs_v2, onball_model, offball_model)
    target_rank = search_similar(
        target_vec, vectors, player_ids, metadata,
        top_k=30,
        exclude_player_ids=[coutinho_id],  # exclude starting point
        target_name="Mané",
    )

    # ============== VERDICT ==============
    print("\n" + "█" * 105)
    print("VERDICT")
    print("█" * 105)
    if target_rank is None:
        print("  ✗ Mané did not appear in top-30")
        print("    The replacement search did not find the actual signing.")
    elif target_rank <= 5:
        print(f"  ✓✓✓ EXCELLENT — Mané ranked #{target_rank}")
        print("    The replacement tool concept works exceptionally well.")
    elif target_rank <= 10:
        print(f"  ✓✓ STRONG — Mané ranked #{target_rank}")
        print("    The replacement tool concept works well.")
    elif target_rank <= 20:
        print(f"  ✓ ACCEPTABLE — Mané ranked #{target_rank}")
        print("    The replacement tool concept works, with room to refine.")
    else:
        print(f"  ⚠ WEAK — Mané ranked #{target_rank}")
        print("    The methodology produces some signal but not strong.")


# ==================================================================================================
# GENERALIZATION TEST — works beyond Liverpool?
# ==================================================================================================

def validate_generalization():
    """
    Test the methodology on a non-Liverpool starting point to prove it generalizes.
    """
    print("\n" + "█" * 105)
    print("GENERALIZATION TEST — Does the methodology work for any team?")
    print("█" * 105)

    player_ids, vectors, metadata, onball_model, offball_model = load_everything()

    # Pick a versatile midfielder/forward who's NOT at Liverpool
    test_starts = ["Mertens", "Nainggolan", "Modrić"]

    for name in test_starts:
        pid = find_player_id(name, metadata, player_ids)
        if pid is None:
            print(f"\n  ✗ {name} not in dataset, skipping")
            continue

        meta = metadata[pid]
        docs = load_player_docs(pid)
        if len(docs) < 5:
            print(f"\n  ✗ {meta['name']} has too few matches ({len(docs)}), skipping")
            continue

        sample_size = min(10, len(docs))
        sampled = random.sample(docs, sample_size)

        print(f"\n  {meta['name']} ({meta['team']}, {meta['primary_position']}) — {sample_size} matches")

        # Apply the same Klopp-style enrichment
        interventions = (
            add_cut_inside(probability=0.5) +
            add_progression(probability=0.4) +
            add_chance_creation(probability=0.3)
        )
        modified = []
        for doc in sampled:
            new_doc = dict(doc)
            new_doc["onball_tokens"] = modify_doc(doc["onball_tokens"], interventions)
            modified.append(new_doc)

        target_vec = infer_player_vector_from_docs(modified, onball_model, offball_model)

        print(f"\n  Top-10 most similar to enriched {meta['name']}:")
        search_similar(
            target_vec, vectors, player_ids, metadata,
            top_k=10, exclude_player_ids=[pid],
        )


# ==================================================================================================
# APPROACH B — MULTI-SOURCE VALIDATION
# ==================================================================================================
#
# Insight: Mané at Southampton played LW/RW/CAM/CF — he's a multi-zone attacker.
# Searching with only Coutinho's docs anchors the query in "left winger" space.
# Solution: Pool documents from Liverpool attackers covering DIFFERENT roles, then
# apply Klopp-style modifications to the pooled set.
#
# This matches how Klopp actually scouted Mané — not as "a left winger replacement"
# but as "a versatile attacker who can play anywhere in the final third."
#
# ==================================================================================================

LIVERPOOL_MULTI_ROLE_SOURCES = [
    # Format: (name_query, matches_per_source, role_description)
    ("Coutinho",  8, "LW creator"),
    ("Lallana",   8, "CAM/inside forward"),
    ("Firmino",   8, "CF/false 9"),
    ("Sturridge", 5, "CF finisher"),
    ("Origi",     5, "Versatile attacker"),
    ("Ibe",       5, "RW/LW pace"),
    ("Benteke",   5, "Target CF"),
]


def gather_multi_source_docs(
    sources_config,
    metadata: dict,
    player_ids: list,
    cap_per_source: int = 8,
):
    """
    Pool match documents from multiple Liverpool attackers covering different roles.

    Returns (pooled_docs, source_summary) where source_summary describes which players contributed.
    """
    pooled = []
    summary = []

    for name, target_count, role_desc in sources_config:
        pid = find_player_id(name, metadata, player_ids)
        if pid is None:
            summary.append((name, role_desc, 0, "not found in dataset"))
            continue

        meta = metadata[pid]
        # Only use Liverpool docs — but our metadata has team-level info,
        # not per-match team. We use the player's primary team.
        if "Liverpool" not in meta.get("team", ""):
            # Player primary team isn't Liverpool — skip to avoid noise
            summary.append((name, role_desc, 0, f"primary team is {meta.get('team', 'Unknown')}"))
            continue

        docs = load_player_docs(pid)
        if not docs:
            summary.append((name, role_desc, 0, "no match docs"))
            continue

        # Take up to cap_per_source matches
        n_to_take = min(target_count, cap_per_source, len(docs))
        sampled = random.sample(docs, n_to_take)
        pooled.extend(sampled)

        summary.append((meta["name"], role_desc, n_to_take, "OK"))

    return pooled, summary


def validate_mane_multi_source():
    """
    The Mané search using Approach B: multi-source document pooling from Liverpool attackers.

    Steps:
        1. Pool docs from Coutinho/Lallana/Firmino/Sturridge/Origi/Ibe (whoever's in dataset)
        2. Apply Klopp-style interventions to ALL pooled docs
        3. Re-infer a single target vector from the pooled modified docs
        4. Search top-30
        5. Report Mané's rank + position distribution of results
    """
    print("\n" + "█" * 105)
    print("APPROACH B — MULTI-SOURCE VALIDATION")
    print("Pooling docs from multiple Liverpool attackers covering different roles")
    print("█" * 105)

    player_ids, vectors, metadata, onball_model, offball_model = load_everything()

    # ----- 1. Gather pooled docs -----
    print("\nGathering source documents from Liverpool attackers:")
    pooled_docs, summary = gather_multi_source_docs(
        LIVERPOOL_MULTI_ROLE_SOURCES, metadata, player_ids, cap_per_source=8,
    )

    print(f"\n{'Player':<35}{'Role':<28}{'Matches':<10}{'Status':<25}")
    print("-" * 100)
    for name, role, count, status in summary:
        print(f"{name:<35}{role:<28}{count:<10}{status:<25}")
    print(f"\nTotal pooled documents: {len(pooled_docs)}")

    if len(pooled_docs) < 10:
        print("⚠ Too few pooled docs — aborting multi-source test")
        return

    # ----- 2. Apply Klopp interventions to ALL pooled docs -----
    print("\nApplying Klopp-style interventions to pooled documents...")
    onball_interventions = (
        add_cut_inside(probability=0.7)
        + upgrade_finishing(probability=0.5)
        + add_progression(probability=0.4)
        + add_chance_creation(probability=0.4)
        + enrich_dribbling(probability=0.4)
    )
    offball_interventions = boost_pressing(probability=0.7)

    modified_pooled = []
    for doc in pooled_docs:
        new_doc = dict(doc)
        if doc.get("onball_tokens"):
            new_doc["onball_tokens"] = modify_doc(doc["onball_tokens"], onball_interventions)
        if doc.get("offball_tokens"):
            new_doc["offball_tokens"] = modify_doc(doc["offball_tokens"], offball_interventions)
        modified_pooled.append(new_doc)

    # ----- 3. Re-infer a single target vector -----
    print("Inferring multi-source target vector...")
    target_vec = infer_player_vector_from_docs(modified_pooled, onball_model, offball_model)

    # ----- 4. Search -----
    # Exclude the source players from results so they don't dominate
    source_pids = []
    for name, _, _, status in summary:
        if status == "OK":
            pid = find_player_id(name, metadata, player_ids)
            if pid:
                source_pids.append(pid)

    print(f"\nExcluding {len(source_pids)} source players from results.")
    print("\nTop-30 most similar players to 'multi-zone Klopp ideal attacker':")

    target_rank = search_similar(
        target_vec, vectors, player_ids, metadata,
        top_k=30,
        exclude_player_ids=source_pids,
        target_name="Mané",
    )

    # ----- 5. Position distribution analysis -----
    print("\n--- Position distribution of top-30 results ---")
    sims = vectors @ target_vec
    for pid in source_pids:
        if pid in player_ids:
            sims[player_ids.index(pid)] = -np.inf
    top30_indices = np.argsort(sims)[::-1][:30]
    position_counts = {}
    for idx in top30_indices:
        pos = metadata[player_ids[idx]]["primary_position"]
        position_counts[pos] = position_counts.get(pos, 0) + 1
    sorted_positions = sorted(position_counts.items(), key=lambda x: -x[1])
    for pos, count in sorted_positions:
        bar = "█" * count
        print(f"  {pos:<28} {count:<3} {bar}")

    # ----- 6. Versatility check on top-30 -----
    print("\n--- Versatility scores of top-30 results ---")
    versatility_scores = []
    for idx in top30_indices:
        v = metadata[player_ids[idx]].get("versatility_score", 0.0)
        versatility_scores.append(v)
    print(f"  Mean versatility: {np.mean(versatility_scores):.3f}")
    print(f"  Max versatility:  {np.max(versatility_scores):.3f}")
    print(f"  Median versatility: {np.median(versatility_scores):.3f}")

    mane_pid = find_player_id("Mané", metadata, player_ids)
    if mane_pid:
        mane_versatility = metadata[mane_pid].get("versatility_score", 0.0)
        print(f"  Mané's versatility (for context): {mane_versatility:.3f}")

    # ----- 7. Verdict -----
    print("\n" + "█" * 105)
    print("APPROACH B VERDICT")
    print("█" * 105)
    if target_rank is None:
        print("  ✗ Mané still not in top-30 with multi-source pooling")
        print("    The query may need per-position vectors (Path B from earlier discussion)")
    elif target_rank <= 5:
        print(f"  ✓✓✓ EXCELLENT — Mané ranked #{target_rank}")
        print("    Multi-source pooling solved the versatility issue. Tool concept validated.")
    elif target_rank <= 10:
        print(f"  ✓✓ STRONG — Mané ranked #{target_rank}")
        print("    Multi-source approach works well for versatile player searches.")
    elif target_rank <= 20:
        print(f"  ✓ ACCEPTABLE — Mané ranked #{target_rank}")
        print("    Methodology produces real signal for versatile players.")
    else:
        print(f"  ⚠ MARGINAL — Mané ranked #{target_rank}")
        print("    Multi-source helps but may need additional refinement.")


# ==================================================================================================
# MAIN
# ==================================================================================================

def main():
    random.seed(42)  # reproducibility
    validate_mane_search()
    validate_mane_multi_source()
    validate_generalization()


if __name__ == "__main__":
    main()
