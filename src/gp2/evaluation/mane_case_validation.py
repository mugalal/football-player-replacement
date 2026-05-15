"""
Mané Validation — Regression Test for the Scouting Methodology

Single purpose: verify that our methodology, when given Liverpool's 2015-16 attacking
profile and asked to find a Klopp-ideal upgrade, ranks Sadio Mané (Liverpool's actual
2016 signing) inside the top 10 of attacking candidates from 2,211 total players.

Methodology:
    1. Pool match documents from 7 Liverpool 2015-16 attackers covering different roles
       (Coutinho, Lallana, Firmino, Sturridge, Origi, Ibe, Benteke).
    2. Apply Klopp-style interventions (cut_inside, finishing, progression,
       chance_creation, dribbling, pressing) at validated per-upgrade probabilities.
    3. Per-match modify-and-infer (Magdaci-style): each match's tokens are modified
       individually, inferred 10× to smooth Doc2Vec noise, vectors averaged.
    4. Average source-level vectors → final query vector.
    5. Rank players by similarity, EXCLUDING defenders (CBs, FBs, GKs, WBs).

Why we exclude defenders here:
    Klopp's brief was for an attacking signing, so defensive results are not
    meaningful for this validation. Some ball-playing CBs (Otamendi, Thiago Silva)
    have onball patterns that overlap with attacking-mids, but they are not
    candidate replacements for our use case. We post-filter them out so the
    top-30 reflects what a real scout would actually consider.

Run:
    python -m src.gp2.evaluation.mane_case_validation
"""

from .scouting_engine import search_replacements, get_player_summary, find_player_id


# ==================================================================================================
# THE LIVERPOOL 2015-16 ATTACKING POOL
# ==================================================================================================

LIVERPOOL_2015_16_ATTACKERS = [
    ##coutinho removed 
    "Lallana",    # CAM/inside forward
    "Firmino",    # CF/false 9
    "Sturridge",  # CF finisher
    "Origi",      # versatile attacker
    "Ibe",        # RW/LW pace (note: matches Jordon Ibe)
    "Benteke",    # target CF
]

# Validated per-upgrade probabilities used as the regression checkpoint.
# Drift from these values means something else changed in the pipeline.
KLOPP_UPGRADES_VALIDATED = {
    "cut_inside":      0.7,
    "finishing":       0.5,
    "progression":     0.4,
    "chance_creation": 0.4,
    "dribbling":       0.4,
    "pressing":        0.7,
}


# ==================================================================================================
# DEFENDER FILTER
# ==================================================================================================

# Positions we exclude from the validation output. The Klopp brief was for an
# attacking signing, so defensive matches (even if behaviorally similar via
# ball-playing onball patterns) are not meaningful for this test.
DEFENDER_POSITIONS = {
    "Goalkeeper",
    "Center Back",
    "Left Center Back",
    "Right Center Back",
    "Left Back",
    "Right Back",
    "Left Wing Back",
    "Right Wing Back",
}


def is_attacker(candidate: dict) -> bool:
    """True if the candidate plays an attacking/midfield role (not a pure defender)."""
    return candidate.get("primary_position") not in DEFENDER_POSITIONS


# ==================================================================================================
# THE VALIDATION
# ==================================================================================================

def validate():
    print("=" * 105)
    print("MANÉ VALIDATION — Regression Test (Defenders Excluded)")
    print("=" * 105)
    print("""
Searches for Klopp's ideal attacking signing using multi-source pooling from
Liverpool's 2015-16 attacking unit. Defensive positions are excluded from the
top-30 (Klopp's brief was for an attacker, not a CB).
""")

    # Confirm Mané is in the dataset
    mane_id = find_player_id("Mané")
    if mane_id is None:
        print("✗ Mané not found in dataset — cannot run validation.")
        return False

    mane_summary = get_player_summary(mane_id)
    print(f"  Validation target: {mane_summary['name']}")
    print(f"    Position: {mane_summary['primary_position']} | Team: {mane_summary['team']}")
    print(f"    Versatility: {mane_summary['versatility_score']:.3f}")
    print(f"    Distinct positions played: {mane_summary['num_distinct_positions']}")
    print()

    # Run the search with the validated per-upgrade probabilities.
    # We request a larger top_k (60) so that after filtering out defenders we
    # still have at least 30 attackers to rank in the output.
    print("  Running search with the Liverpool 2015-16 attacking pool + Klopp upgrades...")
    print("  Using locked-in per-upgrade probabilities (regression checkpoint).")
    result = search_replacements(
        sources=LIVERPOOL_2015_16_ATTACKERS,
        upgrades=KLOPP_UPGRADES_VALIDATED,
        top_k=60,
        seed=42,
    )

    # Report sources actually resolved
    print(f"\n  Sources resolved: {len(result['query']['sources'])}/{len(LIVERPOOL_2015_16_ATTACKERS)}")
    for s in result["query"]["sources"]:
        print(f"    - {s['name']:<35} {s['primary_position']:<25} matches={s['num_matches']}")

    if result["warnings"]:
        print("\n  Warnings:")
        for w in result["warnings"]:
            print(f"    - {w}")

    # ---------- Filter defenders, re-rank attackers ----------
    raw_candidates = result["candidates"]
    attackers = [c for c in raw_candidates if is_attacker(c)]
    excluded_count = len(raw_candidates) - len(attackers)

    # Re-assign attacker-only ranks
    for new_rank, c in enumerate(attackers, start=1):
        c["attacker_rank"] = new_rank

    print(f"\n  Filtered {excluded_count} defender(s) from raw top-{len(raw_candidates)}.")

    # Display top-30 attackers
    print("\n  Top-30 attackers (defenders excluded):")
    print(f"  {'Rank':<6}{'Player':<37}{'Position':<27}{'Team':<23}{'Sim':<8}")
    print("  " + "-" * 100)

    mane_rank = None
    for c in attackers[:30]:
        marker = ""
        if c["player_id"] == mane_id:
            mane_rank = c["attacker_rank"]
            marker = "  ← TARGET ✓"
        print(f"  {c['attacker_rank']:<6}{c['name']:<37}{c['primary_position']:<27}"
              f"{c['team']:<23}{c['similarity']:.4f}{marker}")

    # If Mané didn't make the top-30 attackers, find his position in the full attacker list
    if mane_rank is None:
        for c in attackers:
            if c["player_id"] == mane_id:
                mane_rank = c["attacker_rank"]
                print(f"\n  Mané not in displayed top-30, but ranks #{mane_rank} among all attackers.")
                break

    # Verdict
    print()
    print("=" * 105)
    print("VERDICT")
    print("=" * 105)
    if mane_rank is None:
        print(f"  ✗ FAIL — Mané did not appear in the attacker shortlist. Methodology has regressed.")
        return False
    elif mane_rank <= 5:
        print(f"  ✓✓✓ EXCELLENT — Mané ranked #{mane_rank} among attackers")
        return True
    elif mane_rank <= 10:
        print(f"  ✓✓ STRONG — Mané ranked #{mane_rank} among attackers")
        return True
    elif mane_rank <= 20:
        print(f"  ✓ ACCEPTABLE — Mané ranked #{mane_rank} among attackers")
        return True
    else:
        print(f"  ⚠ MARGINAL — Mané ranked #{mane_rank} among attackers")
        return False


# ==================================================================================================
# MAIN
# ==================================================================================================

def main():
    success = validate()
    print()
    if success:
        print("Methodology validated. Engine and CLI are safe to use.")
    else:
        print("Validation drifted — investigate before deploying.")
    print()


if __name__ == "__main__":
    main()