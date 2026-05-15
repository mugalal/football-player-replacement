"""
Scouting Engine — Reusable Player Replacement / Upgrade Search

Pure engine module: takes inputs, returns ranked candidates. No I/O beyond returns.
Consumed by both the CLI (scout.py) and the future web app.

Public API:
    search_replacements(...)      → ranked list of candidate dicts
    list_available_players(...)   → autocomplete-style player search
    list_available_upgrades()     → upgrade catalog with descriptions
    list_available_filters()      → filter spec
    get_player_summary(...)       → quick info card for a player

Design notes (V3 — fixed inference):
    - For pure similarity (no upgrades): use the STORED player vector directly.
      No re-inference needed. Fast and exact.
    - For modifications/upgrades: use Magdaci's per-match approach. Each match is
      modified individually, inferred 10 times to smooth Doc2Vec noise, then
      vectors are averaged. Tokens stay in their natural per-match documents.
    - Multi-source: pool match-level vectors (NOT tokens) across source players.
    - Default upgrade intensity is 0.5 — kept moderate to avoid the
      offball-saturation bias that surfaces defenders at high values.
    - All randomness uses a per-call seed for reproducibility (web app needs this).

Why we changed: The previous implementation pooled all of a player's tokens into
one shuffled, truncated synthetic doc, then ran ONE inference on it. This produced
vectors that didn't live in the same region of vector space as the stored ones,
causing Suárez/Benzema searches to return Center Backs. The new approach matches
how Magdaci's reference implementation works.
"""

import json
import random
from collections import defaultdict
from typing import List, Dict, Optional

import numpy as np
from gensim.models.doc2vec import Doc2Vec

from .modify_doc import (
    Intervention,
    add_cut_inside,
    upgrade_finishing,
    add_progression,
    add_chance_creation,
    enrich_dribbling,
    boost_pressing,
    aerial_dominance,
    ball_winning,
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
# PATHS
# ==================================================================================================

# ==================================================================================================
# CONFIGURATION
# ==================================================================================================

DEFAULT_UPGRADE_INTENSITY = 0.5
ONBALL_DIM = 48
OFFBALL_DIM = 16

# Inference parameters (per Magdaci's approach)
# - INFERENCE_STEPS: epochs per single inference call. More = more accurate but slower.
# - INFERENCE_REPS: how many times to re-infer each doc and average. Smooths Doc2Vec
#   stochasticity. Magdaci uses 10. Lower = faster, higher = more stable.
INFERENCE_STEPS = 10
INFERENCE_REPS = 10

# Optional cap on matches per source to limit search latency.
# 0 or None = use all matches the player has.
MAX_MATCHES_PER_SOURCE = 25


# ==================================================================================================
# UPGRADE CATALOG — what users can choose from
# ==================================================================================================

UPGRADE_CATALOG = {
    "finishing": {
        "label": "More Clinical Finishing",
        "description": "Converts more shot attempts into goals. Use when you want a more clinical striker.",
        "applies_to": "onball",
        "builder": upgrade_finishing,
    },
    "cut_inside": {
        "label": "Inverted Winger / Cut Inside",
        "description": "Adds cut-inside behavior from wide areas. Use for inverted wingers like Mané or Salah.",
        "applies_to": "onball",
        "builder": add_cut_inside,
    },
    "progression": {
        "label": "Direct Ball Progression",
        "description": "More progressive carries and forward passes. Use when you want a more direct, vertical player.",
        "applies_to": "onball",
        "builder": add_progression,
    },
    "chance_creation": {
        "label": "Chance Creation",
        "description": "More key passes and final-third deliveries. Use when you need a creator.",
        "applies_to": "onball",
        "builder": add_chance_creation,
    },
    "dribbling": {
        "label": "Better Dribbling",
        "description": "More successful dribbles, especially in the box. Use for 1v1 specialists.",
        "applies_to": "onball",
        "builder": enrich_dribbling,
    },
    "pressing": {
        "label": "Counterpressing Intensity",
        "description": "Converts regular pressure into counterpress (Klopp-style gegenpressing).",
        "applies_to": "offball",
        "builder": boost_pressing,
    },
    "aerial_dominance": {
        "label": "Aerial Dominance",
        "description": "Wins more aerial duels. Use for target strikers, headed-goal threats, or aerially strong center backs.",
        "applies_to": "offball",
        "builder": aerial_dominance,
    },
    "ball_winning": {
        "label": "Ball-Winning",
        "description": "Wins more ground duels, interceptions, and recoveries. Use for defensive midfielders or pressing midfielders (Kanté/Casemiro types).",
        "applies_to": "offball",
        "builder": ball_winning,
    },
}


# ==================================================================================================
# FILTER CATALOG — supported filters in v1
# ==================================================================================================

def list_available_filters() -> Dict:
    """Returns supported filter spec for UI building."""
    return {
        "positions": {
            "type": "multi_select",
            "description": "Filter by primary position. If empty, all positions allowed.",
            "field": "primary_position",
        },
        "exclude_teams": {
            "type": "multi_select",
            "description": "Exclude players from these teams (e.g., your own).",
            "field": "team",
        },
        "min_versatility": {
            "type": "float",
            "description": "Minimum versatility score (Shannon entropy across positions).",
            "default": 0.0,
        },
        "max_versatility": {
            "type": "float",
            "description": "Maximum versatility score.",
            "default": None,
        },
        "min_matches": {
            "type": "int",
            "description": "Minimum number of matches in the dataset.",
            "default": 5,
        },
    }


# ==================================================================================================
# DATA LOADING — module-level cache
# ==================================================================================================

_cache = {
    "player_ids": None,
    "vectors": None,
    "metadata": None,
    "name_to_id": None,
    "onball_model": None,
    "offball_model": None,
}


def _ensure_loaded():
    """Idempotent: loads everything once, caches in module state."""
    if _cache["player_ids"] is not None:
        return

    data = np.load(PLAYER2VEC_PATH)
    _cache["player_ids"] = list(data["player_ids"])
    _cache["vectors"] = data["vectors"]

    with open(PLAYER_METADATA_PATH, "r", encoding="utf-8") as f:
        _cache["metadata"] = json.load(f)

    # Lowercase name-to-id index for fast lookup
    name_to_id = {}
    for pid in _cache["player_ids"]:
        name = _cache["metadata"].get(pid, {}).get("name", "")
        if name:
            name_to_id[name.lower()] = pid
    _cache["name_to_id"] = name_to_id

    _cache["onball_model"] = Doc2Vec.load(str(ONBALL_MODEL_PATH))
    _cache["offball_model"] = Doc2Vec.load(str(OFFBALL_MODEL_PATH))


# ==================================================================================================
# PLAYER LOOKUP
# ==================================================================================================

def list_available_players(query: str = "", limit: int = 20) -> List[Dict]:
    """
    Autocomplete-style player search. Returns matching players with their IDs.
    Empty query returns first `limit` players alphabetically.
    """
    _ensure_loaded()
    metadata = _cache["metadata"]
    player_ids = _cache["player_ids"]

    query_lower = query.lower().strip()
    matches = []
    for pid in player_ids:
        meta = metadata.get(pid, {})
        name = meta.get("name", "")
        if not query_lower or query_lower in name.lower():
            matches.append({
                "player_id": pid,
                "name": name,
                "primary_position": meta.get("primary_position", "Unknown"),
                "team": meta.get("team", "Unknown"),
                "versatility_score": meta.get("versatility_score", 0.0),
                "num_matches": meta.get("num_matches", 0),
            })

    matches.sort(key=lambda m: m["name"])
    return matches[:limit]


def find_player_id(query: str) -> Optional[str]:
    """
    Resolve a single player by name query. Prefers exact match.
    Returns None if not found, returns first match if multiple.
    """
    _ensure_loaded()
    name_to_id = _cache["name_to_id"]
    query_lower = query.lower().strip()

    if query_lower in name_to_id:
        return name_to_id[query_lower]

    # Partial match
    for name, pid in name_to_id.items():
        if query_lower in name:
            return pid
    return None


def get_player_summary(player_id_or_name: str) -> Optional[Dict]:
    """Quick info card for a player. Accepts ID or name."""
    _ensure_loaded()
    metadata = _cache["metadata"]

    pid = player_id_or_name if player_id_or_name in metadata else find_player_id(player_id_or_name)
    if pid is None or pid not in metadata:
        return None

    meta = metadata[pid]
    return {
        "player_id": pid,
        "name": meta.get("name"),
        "primary_position": meta.get("primary_position"),
        "team": meta.get("team"),
        "versatility_score": meta.get("versatility_score", 0.0),
        "num_distinct_positions": meta.get("num_distinct_positions", 1),
        "num_matches": meta.get("num_matches", 0),
        "position_distribution": meta.get("position_distribution", {}),
    }


# ==================================================================================================
# UPGRADE CATALOG ACCESS
# ==================================================================================================

def list_available_upgrades() -> List[Dict]:
    """Returns the upgrade catalog, formatted for UI display."""
    return [
        {
            "key": key,
            "label": spec["label"],
            "description": spec["description"],
            "applies_to": spec["applies_to"],
        }
        for key, spec in UPGRADE_CATALOG.items()
    ]


def _build_interventions(upgrades, intensity: float):
    """
    Build the actual intervention objects from upgrade specifications.

    Args:
        upgrades:  Either a list of upgrade keys (using uniform `intensity`),
                   or a dict mapping keys to per-upgrade probabilities.
        intensity: Uniform probability used when `upgrades` is a list.
                   Ignored when `upgrades` is a dict.

    Returns:
        (onball_interventions, offball_interventions)
    """
    onball = []
    offball = []

    if isinstance(upgrades, dict):
        upgrade_specs = upgrades.items()  # (key, probability) pairs
    else:
        upgrade_specs = [(key, intensity) for key in upgrades]

    for key, prob in upgrade_specs:
        if key not in UPGRADE_CATALOG:
            raise ValueError(f"Unknown upgrade: {key}. Available: {list(UPGRADE_CATALOG.keys())}")
        spec = UPGRADE_CATALOG[key]
        built = spec["builder"](probability=prob)
        if spec["applies_to"] == "onball":
            onball.extend(built)
        else:
            offball.extend(built)

    return onball, offball


# ==================================================================================================
# DOCUMENT LOADING & MODIFICATION
# ==================================================================================================

def _load_player_docs(player_id: str) -> List[dict]:
    """Stream the corpus and pick out one player's match documents."""
    docs = []
    with open(DOCS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line.strip())
            if d["player_id"] == player_id:
                docs.append(d)
    return docs


def _sample_player_matches(
    player_id: str,
    rng: random.Random,
    max_matches: int = MAX_MATCHES_PER_SOURCE,
) -> List[dict]:
    """
    Load all of a player's match docs, optionally cap to max_matches via random sampling.
    Each doc keeps its natural per-match structure — we do NOT pool tokens.
    """
    docs = _load_player_docs(player_id)
    if not docs:
        return []
    if max_matches and len(docs) > max_matches:
        docs = rng.sample(docs, max_matches)
    return docs


# ==================================================================================================
# VECTOR INFERENCE — Magdaci-style per-match approach
# ==================================================================================================
# Key principle: each match document stays intact. We infer one vector PER MATCH, with multiple
# repetitions to smooth Doc2Vec inference noise, then average across matches.
# We never pool tokens across matches into one synthetic super-doc.
# ==================================================================================================


def _estimate_match_vector(
    onball_tokens: List[str],
    offball_tokens: List[str],
    reps: int = INFERENCE_REPS,
    steps: int = INFERENCE_STEPS,
) -> np.ndarray:
    """
    Infer the 64D vector for ONE match document.
    Runs `reps` inferences and averages to reduce Doc2Vec stochastic noise.
    Returns an unnormalized 64D vector.
    """
    onball_model = _cache["onball_model"]
    offball_model = _cache["offball_model"]

    on_reps = []
    off_reps = []

    if onball_tokens:
        for _ in range(reps):
            on_reps.append(onball_model.infer_vector(onball_tokens, epochs=steps))
    if offball_tokens:
        for _ in range(reps):
            off_reps.append(offball_model.infer_vector(offball_tokens, epochs=steps))

    mean_on = np.mean(on_reps, axis=0) if on_reps else np.zeros(ONBALL_DIM)
    mean_off = np.mean(off_reps, axis=0) if off_reps else np.zeros(OFFBALL_DIM)

    return np.concatenate([mean_on, mean_off])


def _player_vector_via_per_match_inference(
    player_id: str,
    rng: random.Random,
    onball_interventions: list = None,
    offball_interventions: list = None,
    max_matches: int = MAX_MATCHES_PER_SOURCE,
) -> Optional[np.ndarray]:
    """
    Build a player's 64D vector by re-inferring each of their matches, then averaging.

    If interventions are provided, each match's tokens are modified BEFORE inference.
    Each match keeps its natural document structure (no token pooling, no shuffling).

    Returns the averaged 64D vector (unnormalized), or None if no usable matches.
    """
    docs = _sample_player_matches(player_id, rng, max_matches)
    if not docs:
        return None

    match_vectors = []
    for doc in docs:
        on_tokens = list(doc.get("onball_tokens") or [])
        off_tokens = list(doc.get("offball_tokens") or [])

        # Apply interventions per-match if requested (Magdaci-style)
        if onball_interventions and on_tokens:
            on_tokens = modify_doc(on_tokens, onball_interventions)
        if offball_interventions and off_tokens:
            off_tokens = modify_doc(off_tokens, offball_interventions)

        if not on_tokens:
            continue  # skip docs with no onball signal at all

        match_vec = _estimate_match_vector(on_tokens, off_tokens)
        match_vectors.append(match_vec)

    if not match_vectors:
        return None

    return np.mean(match_vectors, axis=0)


# ==================================================================================================
# FILTERING
# ==================================================================================================

def _passes_filters(meta: dict, filters: Dict) -> bool:
    """Check if a player's metadata passes the user-specified filters."""
    if not filters:
        return True

    if "positions" in filters and filters["positions"]:
        if meta.get("primary_position") not in filters["positions"]:
            return False

    if "exclude_teams" in filters and filters["exclude_teams"]:
        if meta.get("team") in filters["exclude_teams"]:
            return False

    if "min_versatility" in filters and filters["min_versatility"] is not None:
        if meta.get("versatility_score", 0.0) < filters["min_versatility"]:
            return False

    if "max_versatility" in filters and filters["max_versatility"] is not None:
        if meta.get("versatility_score", 0.0) > filters["max_versatility"]:
            return False

    if "min_matches" in filters and filters["min_matches"] is not None:
        if meta.get("num_matches", 0) < filters["min_matches"]:
            return False

    return True


# ==================================================================================================
# THE MAIN SEARCH FUNCTION
# ==================================================================================================

def search_replacements(
    sources: List[str],
    upgrades=None,
    upgrade_intensity: float = DEFAULT_UPGRADE_INTENSITY,
    top_k: int = 30,
    filters: Dict = None,
    exclude_sources: bool = True,
    seed: int = 42,
) -> Dict:
    """
    Search for replacement / upgrade candidates.

    Args:
        sources:           One or more player names or IDs to use as the search base.
                           1 source = single-player upgrade. 2+ = multi-source pooling.
        upgrades:          Either:
                             - List[str] of upgrade keys (uniform intensity), e.g.
                               ["cut_inside", "finishing"]
                             - Dict[str, float] mapping keys to per-upgrade probabilities,
                               e.g. {"cut_inside": 0.7, "finishing": 0.5}
                             - None or empty list = no modification.
        upgrade_intensity: Uniform probability when `upgrades` is a list. Default 0.5.
                           Ignored when `upgrades` is a dict.
        top_k:             Number of candidates to return.
        filters:           Optional dict of filters (see list_available_filters()).
        exclude_sources:   If True, exclude the source players from results.
        seed:              RNG seed for reproducibility.

    Returns:
        {
            "query": {
                "sources": [...resolved player info...],
                "upgrades": [...] or {...},
                "upgrade_intensity": 0.5,
                "filters": {...},
            },
            "candidates": [
                {"rank": 1, "player_id": ..., "name": ..., "primary_position": ...,
                 "team": ..., "similarity": ..., "versatility_score": ...},
                ...
            ],
            "warnings": [...]   // any non-fatal issues
        }
    """
    _ensure_loaded()
    rng = random.Random(seed)

    if not sources:
        raise ValueError("At least one source player is required.")

    # Normalize upgrades input
    if upgrades is None:
        upgrades = []
    filters = filters or {}
    warnings = []

    # ---------- Resolve source players ----------
    resolved_sources = []
    source_pids = []
    for src in sources:
        pid = src if src in _cache["metadata"] else find_player_id(src)
        if pid is None:
            warnings.append(f"Source not found: '{src}' — skipping.")
            continue
        resolved_sources.append(get_player_summary(pid))
        source_pids.append(pid)

    if not resolved_sources:
        raise ValueError("No valid source players resolved. Aborting.")

    # ---------- Build interventions (if any) ----------
    has_upgrades = bool(upgrades) and (len(upgrades) > 0 if isinstance(upgrades, (list, dict)) else False)
    if has_upgrades:
        onball_interventions, offball_interventions = _build_interventions(upgrades, upgrade_intensity)
    else:
        onball_interventions, offball_interventions = [], []

    # ---------- Build target vector ----------
    # Two paths:
    #   (1) No upgrades → use the STORED player vector(s) directly. Skip inference entirely.
    #       Stored vectors are the result of training; using them is exact and fast.
    #   (2) With upgrades → use Magdaci's per-match approach. Each source player's matches
    #       are modified individually, inferred with multiple repetitions, then averaged.
    vectors = _cache["vectors"]
    player_ids = _cache["player_ids"]
    metadata = _cache["metadata"]

    if not has_upgrades:
        # FAST PATH — use stored vectors. Average across multiple sources if given.
        per_source_vectors = []
        for pid in source_pids:
            if pid not in player_ids:
                warnings.append(f"Source {pid} not in stored player2vec — skipping.")
                continue
            per_source_vectors.append(vectors[player_ids.index(pid)])
        if not per_source_vectors:
            raise ValueError("None of the sources have stored vectors.")
        target_vec = np.mean(per_source_vectors, axis=0)
    else:
        # MODIFICATION PATH — Magdaci-style per-match inference per source, then average.
        per_source_vectors = []
        for pid in source_pids:
            v = _player_vector_via_per_match_inference(
                pid, rng,
                onball_interventions=onball_interventions,
                offball_interventions=offball_interventions,
                max_matches=MAX_MATCHES_PER_SOURCE,
            )
            if v is None:
                warnings.append(f"No usable docs for source: {pid}")
                continue
            per_source_vectors.append(v)
        if not per_source_vectors:
            raise ValueError("None of the sources had usable documents.")
        target_vec = np.mean(per_source_vectors, axis=0)

    # Normalize target vector (stored vectors are unit-length, so this matches)
    target_vec = target_vec / np.clip(np.linalg.norm(target_vec), 1e-8, None)

    # ---------- Search ----------
    sims = vectors @ target_vec

    # Exclude sources from results
    if exclude_sources:
        for pid in source_pids:
            if pid in player_ids:
                sims[player_ids.index(pid)] = -np.inf

    # Apply filters by setting non-passing players to -inf
    if filters:
        for i, pid in enumerate(player_ids):
            meta = metadata.get(pid, {})
            if not _passes_filters(meta, filters):
                sims[i] = -np.inf

    # Rank and assemble candidates
    ranked_indices = np.argsort(sims)[::-1]
    candidates = []
    for rank, idx in enumerate(ranked_indices[:top_k], 1):
        if not np.isfinite(sims[idx]):
            break  # all remaining are filtered out
        pid = player_ids[idx]
        meta = metadata[pid]
        candidates.append({
            "rank": rank,
            "player_id": pid,
            "name": meta.get("name"),
            "primary_position": meta.get("primary_position"),
            "team": meta.get("team"),
            "similarity": float(sims[idx]),
            "versatility_score": meta.get("versatility_score", 0.0),
            "num_matches": meta.get("num_matches", 0),
        })

    return {
        "query": {
            "sources": resolved_sources,
            "upgrades": upgrades,
            "upgrade_intensity": upgrade_intensity,
            "filters": filters,
            "seed": seed,
        },
        "candidates": candidates,
        "warnings": warnings,
    }
