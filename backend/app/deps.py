"""Shared FastAPI dependencies."""
from __future__ import annotations

from fastapi import HTTPException, status

from app.services import engine


def require_engine() -> None:
    """Raise 503 if the engine is not in the 'ready' state."""
    if engine.engine_state != "ready":
        detail = f"Engine unavailable: {engine.engine_message or 'not loaded'}"
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)
