"""
Player Analogies — Vector Arithmetic Validation

Tests if the Player2Vec embedding space encodes football semantics meaningfully.
Inspired by Magdaci's PlayersAnalogies and the classic word2vec
"king - man + woman ≈ queen" demonstration.

Examples:
    Suárez - Messi + Neymar ≈ ?     (forward who plays alongside playmakers)
    Alba   - Piqué + Ramos  ≈ ?     (modern fullback)
    Iniesta - Xavi + Modrić ≈ ?     (creative midfielder)

If results make football sense, the embedding space is meaningful.
If results are random, something is structurally wrong.
"""

import json
import numpy as np
from typing import List, Optional

from src.gp2.paths import PLAYER2VEC_PATH, PLAYER_METADATA_PATH


# ==================================================================================================
# DATA LOADING
# ==================================================================================================

def load_player2vec():
    """Returns (player_ids, vectors, metadata_dict, name_to_idx)."""
    data = np.load(PLAYER2VEC_PATH)
    player_ids = list(data["player_ids"])
    vectors = data["vectors"]

    with open(PLAYER_METADATA_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    # Build name → index lookup (lowercase substring matching)
    name_to_idx = {}
    for i, pid in enumerate(player_ids):
        name = metadata.get(pid, {}).get("name", "")
        if name:
            name_to_idx[name.lower()] = i

    return player_ids, vectors, metadata, name_to_idx


def find_player(name_query: str, name_to_idx: dict) -> Optional[int]:
    """Find player index by partial name match. Returns None if not found or ambiguous."""
    query = name_query.lower()

    # Exact match first
    if query in name_to_idx:
        return name_to_idx[query]

    # Substring match
    matches = [(name, idx) for name, idx in name_to_idx.items() if query in name]
    if len(matches) == 1:
        return matches[0][1]
    elif len(matches) > 1:
        print(f"  ⚠ Ambiguous: '{name_query}' matches {len(matches)} players. Showing first 3:")
        for name, idx in matches[:3]:
            print(f"      - {name}")
        return matches[0][1]  # use first match
    else:
        return None


# ==================================================================================================
# ANALOGY COMPUTATION
# ==================================================================================================

def analogy(
    player_a: str,
    player_minus: str,
    player_plus: str,
    top_k: int = 10,
    exclude_inputs: bool = True,
):
    """
    Compute: vec(A) - vec(MINUS) + vec(PLUS), find top-K most similar players.
    Reads as: "A is to MINUS as ? is to PLUS"
    Or:       "A but in PLUS's context instead of MINUS's"
    """
    player_ids, vectors, metadata, name_to_idx = load_player2vec()

    # Find input players
    idx_a = find_player(player_a, name_to_idx)
    idx_minus = find_player(player_minus, name_to_idx)
    idx_plus = find_player(player_plus, name_to_idx)

    missing = []
    if idx_a is None: missing.append(player_a)
    if idx_minus is None: missing.append(player_minus)
    if idx_plus is None: missing.append(player_plus)
    if missing:
        print(f"  ✗ Could not find: {', '.join(missing)}")
        return None

    # Vector arithmetic
    target = vectors[idx_a] - vectors[idx_minus] + vectors[idx_plus]
    target = target / np.linalg.norm(target)

    # Cosine similarity (vectors are already normalized post-dominant-removal)
    sims = vectors @ target

    # Exclude input players
    if exclude_inputs:
        sims[idx_a] = -np.inf
        sims[idx_minus] = -np.inf
        sims[idx_plus] = -np.inf

    top_indices = np.argsort(sims)[::-1][:top_k]

    a_meta = metadata[player_ids[idx_a]]
    m_meta = metadata[player_ids[idx_minus]]
    p_meta = metadata[player_ids[idx_plus]]

    print(f"\n{'='*100}")
    print(f"  {a_meta['name']} ({a_meta['primary_position']}) "
          f"- {m_meta['name']} ({m_meta['primary_position']}) "
          f"+ {p_meta['name']} ({p_meta['primary_position']}) ≈ ?")
    print(f"{'='*100}")
    print(f"{'Rank':<6}{'Player':<40}{'Position':<28}{'Team':<24}{'Sim':<8}")
    print("-" * 105)

    results = []
    for rank, idx in enumerate(top_indices, 1):
        meta = metadata[player_ids[idx]]
        print(f"{rank:<6}{meta['name']:<40}{meta['primary_position']:<28}{meta['team']:<24}{sims[idx]:.4f}")
        results.append({
            "rank": rank,
            "name": meta["name"],
            "position": meta["primary_position"],
            "team": meta["team"],
            "similarity": float(sims[idx]),
        })

    return results


# ==================================================================================================
# PRESET ANALOGY SUITES
# ==================================================================================================

ANALOGY_TESTS = [
    # Position translation tests
    ("Suárez",  "Messi",   "Neymar"),       # forward in different attacking context
    ("Alba",    "Piqué",   "Ramos"),        # left back to right back-ish via Ramos
    ("Iniesta", "Xavi",    "Modrić"),       # midfielder swap

    # Team-context translation
    ("Neymar",  "Messi",   "Suárez"),       # winger when paired with finisher instead of playmaker
    ("Coutinho","Henderson","Wijnaldum"),  # Liverpool internal swap

    # Style translation
    ("Mané",    "Lallana", "Coutinho"),     # versatile attacker swapped between Liverpool styles

    # Simple sanity (player should map close to similar role players)
    ("Ronaldo", "Messi",   "Neymar"),       # if both Ronaldos exist this might be ambiguous
]


def run_analogy_suite():
    """Run a battery of analogies and print results."""
    print("\n" + "█" * 100)
    print("PLAYER ANALOGIES — Vector Arithmetic Sanity Check")
    print("█" * 100)
    print("\nTesting whether the embedding space captures football semantics.")
    print("Good results = related/sensible players appear at the top.\n")

    for a, minus, plus in ANALOGY_TESTS:
        analogy(a, minus, plus, top_k=5)


# ==================================================================================================
# MAIN
# ==================================================================================================

def main():
    run_analogy_suite()


if __name__ == "__main__":
    main()
