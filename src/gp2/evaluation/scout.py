"""
Interactive CLI for the Scouting Engine

Wraps scouting_engine.py with a simple terminal UI for testing and experimentation.
Same engine the web app will use — this just gives a terminal way to drive it.

Run:
    python -m src.gp2.evaluation.scout
"""

from typing import List, Dict, Optional

from .scouting_engine import (
    search_replacements,
    list_available_players,
    list_available_upgrades,
    list_available_filters,
    get_player_summary,
    find_player_id,
    DEFAULT_UPGRADE_INTENSITY,
)


# ==================================================================================================
# DISPLAY HELPERS
# ==================================================================================================

def _hr(char: str = "─", width: int = 100):
    print(char * width)


def _section(title: str):
    print()
    _hr("█")
    print(f"  {title}")
    _hr("█")


def _print_player(p: Dict, prefix: str = ""):
    print(f"{prefix}{p['name']:<35} {p['primary_position']:<28} {p['team']:<25} "
          f"matches={p['num_matches']:<4} versatility={p['versatility_score']:.3f}")


# ==================================================================================================
# INTERACTIVE PROMPTS
# ==================================================================================================

def prompt_player(prompt_label: str = "Player") -> Optional[str]:
    """
    Prompt for a player by name. Shows matches, lets user pick by number.
    Returns player_id, or None if user cancels.
    """
    while True:
        query = input(f"  {prompt_label} (name, partial OK; blank to cancel): ").strip()
        if not query:
            return None

        matches = list_available_players(query=query, limit=10)
        if not matches:
            print(f"    No players matching '{query}'. Try again.")
            continue

        if len(matches) == 1:
            chosen = matches[0]
            _print_player(chosen, prefix="  ✓ Selected: ")
            return chosen["player_id"]

        print(f"    Multiple matches ({len(matches)}):")
        for i, m in enumerate(matches, 1):
            print(f"      [{i}] {m['name']:<35} {m['primary_position']:<25} {m['team']:<22}")
        print(f"      [0] Cancel / search again")

        choice = input("    Pick number: ").strip()
        if not choice.isdigit():
            print("    Invalid input.")
            continue
        choice_int = int(choice)
        if choice_int == 0:
            continue
        if 1 <= choice_int <= len(matches):
            chosen = matches[choice_int - 1]
            _print_player(chosen, prefix="  ✓ Selected: ")
            return chosen["player_id"]
        print("    Out of range.")


def prompt_sources() -> List[str]:
    """Loop to collect 1+ source players."""
    print("\nSelect source player(s). 1 = single upgrade, 2+ = multi-source pooling (recommended for versatile profiles).")
    sources = []
    while True:
        label = f"Source #{len(sources) + 1}" if sources else "Source player"
        pid = prompt_player(prompt_label=label)
        if pid is None:
            if not sources:
                print("  At least one source is required.")
                continue
            break
        sources.append(pid)
        more = input("  Add another source? (y/N): ").strip().lower()
        if more != "y":
            break
    return sources


def prompt_upgrades() -> List[str]:
    """Show upgrade catalog and let user pick multiple."""
    catalog = list_available_upgrades()
    print("\nAvailable upgrades (apply changes to source profile before searching):")
    for i, u in enumerate(catalog, 1):
        print(f"  [{i}] {u['label']:<35}  ({u['applies_to']})")
        print(f"      {u['description']}")
    print(f"  [0] Done — no more upgrades")

    selected = []
    while True:
        choice = input("  Pick upgrade by number (0 to finish): ").strip()
        if not choice.isdigit():
            print("    Invalid input.")
            continue
        choice_int = int(choice)
        if choice_int == 0:
            break
        if 1 <= choice_int <= len(catalog):
            key = catalog[choice_int - 1]["key"]
            if key in selected:
                print(f"    Already selected. Skipping.")
            else:
                selected.append(key)
                print(f"    + {catalog[choice_int - 1]['label']}")
        else:
            print("    Out of range.")

    return selected


def prompt_intensity_mode(selected_upgrades: List[str]):
    """
    Ask how the user wants to apply intensity.

    Returns a tuple (upgrades_param, intensity_param):
        - upgrades_param is either the original list (uniform mode) or a dict (per-upgrade)
        - intensity_param is the float (used only with the list form)
    """
    if not selected_upgrades:
        return [], DEFAULT_UPGRADE_INTENSITY

    print("\nIntensity mode:")
    print(f"  [1] Uniform intensity for all upgrades  (default — moderate value {DEFAULT_UPGRADE_INTENSITY})")
    print(f"  [2] Custom per-upgrade probabilities    (advanced)")
    choice = input("  Pick (default 1): ").strip()

    if choice == "2":
        # Per-upgrade tuning
        per_upgrade = {}
        print("\n  Set probability for each upgrade (0.0 to 1.0). Press Enter to use 0.5.")
        for key in selected_upgrades:
            raw = input(f"    {key}: ").strip()
            if not raw:
                per_upgrade[key] = DEFAULT_UPGRADE_INTENSITY
            else:
                try:
                    val = float(raw)
                    val = max(0.0, min(1.0, val))
                    per_upgrade[key] = val
                except ValueError:
                    print(f"      Invalid number, using {DEFAULT_UPGRADE_INTENSITY}.")
                    per_upgrade[key] = DEFAULT_UPGRADE_INTENSITY
        return per_upgrade, DEFAULT_UPGRADE_INTENSITY

    # Uniform mode (default)
    raw = input(f"  Intensity (0.0 to 1.0, default {DEFAULT_UPGRADE_INTENSITY}): ").strip()
    if not raw:
        return selected_upgrades, DEFAULT_UPGRADE_INTENSITY
    try:
        val = float(raw)
        val = max(0.0, min(1.0, val))
        return selected_upgrades, val
    except ValueError:
        print(f"    Invalid number, using {DEFAULT_UPGRADE_INTENSITY}.")
        return selected_upgrades, DEFAULT_UPGRADE_INTENSITY


def prompt_filters() -> Dict:
    """Optionally collect filters."""
    apply_filters = input("\nApply filters? (y/N): ").strip().lower()
    if apply_filters != "y":
        return {}

    filters = {}

    # Position filter
    pos_input = input("  Filter by positions? Comma-separated (e.g., 'Left Wing, Right Wing'). Blank = all: ").strip()
    if pos_input:
        filters["positions"] = [p.strip() for p in pos_input.split(",") if p.strip()]

    # Exclude teams
    excl_input = input("  Exclude teams? Comma-separated. Blank = none: ").strip()
    if excl_input:
        filters["exclude_teams"] = [t.strip() for t in excl_input.split(",") if t.strip()]

    # Versatility floor
    minver = input("  Minimum versatility score? (e.g., 0.5; blank = no minimum): ").strip()
    if minver:
        try:
            filters["min_versatility"] = float(minver)
        except ValueError:
            print("    Invalid number, skipping.")

    # Min matches
    minmatches = input("  Minimum matches in dataset? (e.g., 10; blank = 5): ").strip()
    if minmatches:
        try:
            filters["min_matches"] = int(minmatches)
        except ValueError:
            print("    Invalid number, skipping.")

    return filters


def prompt_top_k(default: int = 20) -> int:
    raw = input(f"\nHow many results to show? (default {default}): ").strip()
    if not raw:
        return default
    try:
        return max(1, int(raw))
    except ValueError:
        return default


# ==================================================================================================
# DISPLAY RESULTS
# ==================================================================================================

def display_results(result: Dict):
    """Pretty-print the engine's response."""
    _section("QUERY SUMMARY")

    sources = result["query"]["sources"]
    print(f"  Source player(s): {len(sources)}")
    for s in sources:
        _print_player(s, prefix="    - ")

    upgrades = result["query"]["upgrades"]
    if upgrades:
        intensity = result["query"]["upgrade_intensity"]
        if isinstance(upgrades, dict):
            print(f"\n  Upgrades applied (per-upgrade probabilities):")
            for k, v in upgrades.items():
                print(f"    - {k:<25} (p={v})")
        else:
            print(f"\n  Upgrades applied (uniform intensity={intensity}):")
            for u in upgrades:
                print(f"    - {u}")
    else:
        print("\n  No upgrades applied (pure similarity search)")

    filters = result["query"]["filters"]
    if filters:
        print(f"\n  Filters:")
        for k, v in filters.items():
            print(f"    - {k}: {v}")

    if result["warnings"]:
        print("\n  ⚠ Warnings:")
        for w in result["warnings"]:
            print(f"    - {w}")

    _section("CANDIDATES")
    candidates = result["candidates"]
    if not candidates:
        print("  No candidates returned. Filters may be too restrictive.")
        return

    print(f"  {'Rank':<6}{'Player':<35}{'Position':<27}{'Team':<23}{'Sim':<8}{'Vers':<6}")
    _hr("-")
    for c in candidates:
        print(f"  {c['rank']:<6}{c['name']:<35}{c['primary_position']:<27}"
              f"{c['team']:<23}{c['similarity']:.4f}  {c['versatility_score']:<6.3f}")

    # Summary stats
    print()
    positions = [c["primary_position"] for c in candidates]
    pos_counts = {}
    for p in positions:
        pos_counts[p] = pos_counts.get(p, 0) + 1
    sorted_pos = sorted(pos_counts.items(), key=lambda x: -x[1])
    print(f"  Position distribution: {', '.join(f'{p}({n})' for p, n in sorted_pos)}")


# ==================================================================================================
# MAIN INTERACTIVE FLOW
# ==================================================================================================

def main():
    _section("SCOUTING ENGINE — Interactive CLI")
    print("\nThis tool searches for replacement / upgrade candidates based on a source profile.")
    print("Steps: pick source(s) → pick upgrades → optionally filter → see results.\n")

    while True:
        sources = prompt_sources()
        upgrades_selected = prompt_upgrades()
        upgrades_param, intensity_param = prompt_intensity_mode(upgrades_selected)
        filters = prompt_filters()
        top_k = prompt_top_k()

        try:
            print("\n  Running search...")
            result = search_replacements(
                sources=sources,
                upgrades=upgrades_param,
                upgrade_intensity=intensity_param,
                top_k=top_k,
                filters=filters,
            )
            display_results(result)
        except ValueError as e:
            print(f"\n  ✗ Error: {e}")

        again = input("\n\nRun another search? (y/N): ").strip().lower()
        if again != "y":
            print("\n  Done.\n")
            break


if __name__ == "__main__":
    main()