"""
/api/validations/mane — the Mané regression check, surfaced as an API endpoint.

Reproduces the config from src/gp2/evaluation/mane_case_validation.py without
importing its `validate()` function. Post-filters defenders, re-ranks
attackers, finds Mané's attacker_rank, returns a verdict.

Cache: deterministic (single variant, seed-fixed), so we cache the response
in module state after the first successful run. Double-checked-lock pattern
prevents two simultaneous cold-cache callers from each running the ~30–60 s
inference.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.deps import require_engine
from app.services import engine
from app.services.heatmap import NUM_ZONES, aggregate_heatmap, player_heatmap
from app.services.mane_preset import (
    DEFENDER_POSITIONS,
    KLOPP_UPGRADES_VALIDATED,
    LIVERPOOL_2015_16_ATTACKERS,
    MANE_FINAL_TOP_N,
    MANE_SEED,
    MANE_TOP_K,
)

logger = logging.getLogger(__name__)
router = APIRouter()

_mane_cache: dict[str, Any] | None = None
_mane_lock = asyncio.Lock()


def _verdict_for(rank: int | None) -> tuple[str, str]:
    if rank is None:
        return (
            "FAIL",
            "Mané did not appear in the post-filtered attacker candidate pool.",
        )
    if rank <= 5:
        return ("EXCELLENT", f"Mané ranked #{rank} among attackers — methodology strongly recovers Liverpool's actual 2016 signing.")
    if rank <= 10:
        return ("STRONG", f"Mané ranked #{rank} among attackers — methodology cleanly recovers Liverpool's actual 2016 signing.")
    if rank <= 20:
        return ("ACCEPTABLE", f"Mané ranked #{rank} among attackers — methodology recovers Liverpool's actual 2016 signing, with noise.")
    if rank <= MANE_FINAL_TOP_N:
        return ("MARGINAL", f"Mané ranked #{rank} among attackers — within the top {MANE_FINAL_TOP_N} but on the edge.")
    return (
        "FAIL",
        f"Mané ranked #{rank} — outside the top {MANE_FINAL_TOP_N} attackers.",
    )


def _build_response(engine_result: dict[str, Any]) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = engine_result.get("candidates", []) or []
    warnings: list[str] = engine_result.get("warnings", []) or []

    attackers = [c for c in candidates if c.get("primary_position") not in DEFENDER_POSITIONS]
    filtered_defender_count = len(candidates) - len(attackers)

    mane_rank: int | None = None
    for i, c in enumerate(attackers, start=1):
        c["attacker_rank"] = i
        if mane_rank is None and "Mané" in (c.get("name") or ""):
            mane_rank = i

    top_attackers = attackers[:MANE_FINAL_TOP_N]
    verdict, description = _verdict_for(mane_rank)

    return {
        "query": engine_result.get("query", {}),
        "candidates": top_attackers,
        "mane_rank": mane_rank,
        "verdict": verdict,
        "verdict_description": description,
        "filtered_defender_count": filtered_defender_count,
        "warnings": warnings,
    }


async def _compute() -> dict[str, Any]:
    result = await engine.run_engine(
        engine.scouting_engine.search_replacements,
        sources=LIVERPOOL_2015_16_ATTACKERS,
        upgrades=KLOPP_UPGRADES_VALIDATED,
        top_k=MANE_TOP_K,
        seed=MANE_SEED,
    )
    return _build_response(result)


@router.get("/validations/mane")
async def mane_validation(_: None = Depends(require_engine)) -> dict[str, Any]:
    global _mane_cache
    if _mane_cache is not None:
        return _mane_cache
    async with _mane_lock:
        # Double-checked: another coroutine may have populated the cache while we were
        # waiting on the lock.
        if _mane_cache is not None:
            return _mane_cache
        try:
            response = await _compute()
        except ValueError as e:
            raise HTTPException(400, detail=str(e))
        except Exception as e:
            logger.exception("Mané validation failed")
            raise HTTPException(500, detail=str(e))
        _mane_cache = response
        return _mane_cache


_mane_heatmap_cache: dict[str, Any] | None = None
_mane_heatmap_lock = asyncio.Lock()


@router.get("/validations/mane/heatmap")
async def mane_heatmap(_: None = Depends(require_engine)) -> dict[str, Any]:
    """
    Heatmaps for the Mané validation explainer:
      - `pool`: aggregated zone counts across the 6 Liverpool 2015-16 attackers
      - `mane`: Mané's own zone counts
      - `top_candidates`: heatmaps for the top 5 attacking candidates the
        methodology surfaced (defenders filtered out). Lets the user see
        that all 5 share a similar spatial profile — visual proof of the
        ranking.

    Depends on the main /api/validations/mane having been computed (or
    computes it on demand) so we know who the top-5 attackers are.
    """
    global _mane_heatmap_cache
    if _mane_heatmap_cache is not None:
        return _mane_heatmap_cache
    async with _mane_heatmap_lock:
        if _mane_heatmap_cache is not None:
            return _mane_heatmap_cache

        # Resolve the 6 source player names → player_ids via the engine's
        # name lookup (this is cheap — no model inference required, just a
        # dict scan).
        try:
            source_ids: list[str] = []
            source_names: list[str] = []
            for name in LIVERPOOL_2015_16_ATTACKERS:
                pid = await engine.run_engine(engine.scouting_engine.find_player_id, name)
                if pid is None:
                    continue
                summary = await engine.run_engine(
                    engine.scouting_engine.get_player_summary, pid
                )
                source_ids.append(pid)
                if summary and summary.get("name"):
                    source_names.append(summary["name"])

            # Find Mané by name. The engine's matcher is plain Unicode substring;
            # the accented form is required.
            mane_id = await engine.run_engine(engine.scouting_engine.find_player_id, "Mané")

            pool_counts = await aggregate_heatmap(source_ids)
            mane_counts = await player_heatmap(mane_id) if mane_id else None

            # Top-5 attacking candidates: reuse the main validation result.
            # If it hasn't been computed yet, compute it now (single inference,
            # then cached for both endpoints).
            global _mane_cache
            validation = _mane_cache
            if validation is None:
                validation = await _compute()
                _mane_cache = validation
            top_candidates = []
            for c in (validation.get("candidates") or [])[:5]:
                cid = c.get("player_id")
                if not cid:
                    continue
                counts = await player_heatmap(str(cid))
                if counts is None:
                    continue
                top_candidates.append({
                    "player_id": cid,
                    "name": c.get("name"),
                    "primary_position": c.get("primary_position"),
                    "team": c.get("team"),
                    "similarity": c.get("similarity"),
                    "attacker_rank": c.get("attacker_rank"),
                    "counts": counts,
                    "total": sum(counts),
                    "is_mane": "Mané" in (c.get("name") or ""),
                })

        except FileNotFoundError as e:
            raise HTTPException(503, detail=f"Heatmap data unavailable: {e}")
        except Exception as e:
            logger.exception("Mané heatmap failed")
            raise HTTPException(500, detail=str(e))

        _mane_heatmap_cache = {
            "pool": {
                "counts": pool_counts,
                "total": sum(pool_counts),
                "source_names": source_names,
                "label": "Liverpool 2015-16 attacking pool",
            },
            "mane": {
                "counts": mane_counts,
                "total": sum(mane_counts) if mane_counts else 0,
                "label": "Sadio Mané",
                "player_id": mane_id,
            },
            "top_candidates": top_candidates,
            "num_x": 6,
            "num_y": 3,
            "num_zones": NUM_ZONES,
        }
        return _mane_heatmap_cache
