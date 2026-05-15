"""Static image URL resolution. Missing files → None (frontend uses initials fallback)."""
from __future__ import annotations

import re

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
