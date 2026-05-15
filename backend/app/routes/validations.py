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
