"""Schemas shared across routes."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    engine_loaded: bool
    engine_state: Literal["warming", "ready", "unavailable"]
    engine_message: str | None = None
    uptime_seconds: float


class ErrorResponse(BaseModel):
    detail: str
