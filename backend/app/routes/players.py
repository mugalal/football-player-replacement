"""Player lookup and similar-players endpoints."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.deps import require_engine
from app.services import engine, player_index
from app.services.images import logo_url_for, photo_url_for

logger = logging.getLogger(__name__)

router = APIRouter()


def _attach_images(p: dict[str, Any], request: Request) -> dict[str, Any]:
    p = dict(p)  # don't mutate engine's cache
    p["photo_url"] = photo_url_for(p.get("player_id", ""), request)
    p["team_logo_url"] = logo_url_for(p.get("team"), request)
    return p


@router.get("/players")
async def list_players(
    request: Request,
    q: str = Query("", description="Accent- and case-insensitive substring match on player name."),
    limit: int = Query(20, ge=1, le=50),
    _: None = Depends(require_engine),
) -> list[dict[str, Any]]:
    # Use the local accent-insensitive index instead of calling the engine
    # directly: the engine's matcher does plain Unicode substring, so
    # `q=mane` would miss "Sadio Mané". The index pulls the full player
    # list once via the engine (cheap, no inference), pre-strips accents,
    # then matches in pure Python.
    try:
        await player_index.ensure_built()
        results = player_index.search(q, limit)
    except Exception as e:
        logger.exception("/api/players failed")
        raise HTTPException(500, detail=str(e))
    return [_attach_images(p, request) for p in results]


@router.get("/players/{player_id}")
async def get_player(
    player_id: str,
    request: Request,
    _: None = Depends(require_engine),
) -> dict[str, Any]:
    try:
        summary = await engine.run_engine(engine.scouting_engine.get_player_summary, player_id)
    except Exception as e:
        logger.exception("get_player_summary failed")
        raise HTTPException(500, detail=str(e))
    if summary is None:
        raise HTTPException(404, detail=f"Player not found: {player_id}")
    return _attach_images(summary, request)


@router.get("/players/{player_id}/similar")
async def similar_players(
    player_id: str,
    request: Request,
    top_k: int = Query(10, ge=1, le=100),
    _: None = Depends(require_engine),
) -> list[dict[str, Any]]:
    try:
        result = await engine.run_engine(
            engine.scouting_engine.search_replacements,
            sources=[player_id],
            upgrades=[],
            top_k=top_k,
        )
    except ValueError as e:
        # Engine raises ValueError for unknown sources / no sources resolved.
        raise HTTPException(404, detail=str(e))
    except Exception as e:
        logger.exception("similar search failed")
        raise HTTPException(500, detail=str(e))
    return [_attach_images(c, request) for c in result.get("candidates", [])]
