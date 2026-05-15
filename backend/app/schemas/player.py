"""Player-related schemas. Loose typing on engine-returned fields because
the engine's dicts include some Optional values we surface as-is."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class PlayerSummary(BaseModel):
    player_id: str
    name: str
    primary_position: str
    team: str
    versatility_score: float
    num_matches: int
    photo_url: str | None = None
    team_logo_url: str | None = None


class PlayerDetail(PlayerSummary):
    num_distinct_positions: int
    position_distribution: dict[str, Any]


class Candidate(BaseModel):
    rank: int
    player_id: str
    name: str
    primary_position: str
    team: str
    similarity: float
    versatility_score: float
    num_matches: int
    photo_url: str | None = None
    team_logo_url: str | None = None
