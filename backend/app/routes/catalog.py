"""
/api/upgrades and /api/filters.

Both are model-INDEPENDENT — the underlying engine functions are pure
constant returns and do NOT call _ensure_loaded(). Verified against
src/gp2/evaluation/scouting_engine.py:145 (list_available_filters) and :291
(list_available_upgrades). Safe to call even when engine_state is
'unavailable'.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.services import engine

router = APIRouter()


@router.get("/upgrades")
def get_upgrades() -> dict:
    if engine.scouting_engine is None:
        raise HTTPException(503, detail="Engine module failed to import")
    flat = engine.scouting_engine.list_available_upgrades()
    grouped: dict[str, list[dict]] = {"onball": [], "offball": []}
    for u in flat:
        bucket = u.get("applies_to")
        if bucket in grouped:
            grouped[bucket].append(u)
    return grouped


_COMING_SOON_FILTERS = [
    "min_age",
    "max_age",
    "leagues",
    "min_market_value",
    "max_market_value",
]


@router.get("/filters")
def get_filters() -> dict:
    if engine.scouting_engine is None:
        raise HTTPException(503, detail="Engine module failed to import")
    result = dict(engine.scouting_engine.list_available_filters())
    result["coming_soon"] = _COMING_SOON_FILTERS
    return result
