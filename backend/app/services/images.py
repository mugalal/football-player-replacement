"""Static image URL resolution. Missing files → None (frontend uses initials fallback)."""
from __future__ import annotations

import re
from typing import Any

from fastapi import Request

from app.config import PLAYERS_STATIC_DIR, TEAMS_STATIC_DIR

_SLUG_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def team_slug(team_name: str) -> str:
    s = _SLUG_NON_ALNUM.sub("-", team_name.lower()).strip("-")
    return s or "unknown"


def photo_url_for(player_id: str, request: Request) -> str | None:
    if not player_id:
        return None
    if not (PLAYERS_STATIC_DIR / f"{player_id}.jpg").is_file():
        return None
    return f"{str(request.base_url).rstrip('/')}/static/players/{player_id}.jpg"


def logo_url_for(team_name: str | None, request: Request) -> str | None:
    if not team_name:
        return None
    slug = team_slug(team_name)
    if not (TEAMS_STATIC_DIR / f"{slug}.png").is_file():
        return None
    return f"{str(request.base_url).rstrip('/')}/static/teams/{slug}.png"


def attach_images(p: dict[str, Any], request: Request) -> dict[str, Any]:
    """Return a copy of a player/candidate dict with photo_url + team_logo_url
    populated using the current request's base URL. Safe to call on engine
    output (does not mutate the engine's cache)."""
    out = dict(p)
    out["photo_url"] = photo_url_for(str(p.get("player_id") or ""), request)
    out["team_logo_url"] = logo_url_for(p.get("team"), request)
    return out


def enrich_search_result(result: dict[str, Any], request: Request) -> dict[str, Any]:
    """Add photo_url + team_logo_url to every player in a search-result dict.

    Applies to both `query.sources` (the resolved source players) and the
    `candidates` array. Returns a new dict — does not mutate the input.
    """
    query = dict(result.get("query") or {})
    sources = [attach_images(s, request) for s in (query.get("sources") or [])]
    query["sources"] = sources
    candidates = [attach_images(c, request) for c in (result.get("candidates") or [])]
    return {
        **result,
        "query": query,
        "candidates": candidates,
    }
