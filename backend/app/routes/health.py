"""Health endpoint. Model-independent — always 200 as long as the app imports."""
from __future__ import annotations

import time

from fastapi import APIRouter

from app.schemas.common import HealthResponse
from app.services import engine

router = APIRouter()

# Module-level start time. Set in main.py via _set_start_time on lifespan startup.
_start_time: float = time.monotonic()


def _set_start_time(t: float) -> None:
    global _start_time
    _start_time = t


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        engine_loaded=engine.engine_loaded(),
        engine_state=engine.engine_state,  # type: ignore[arg-type]
        engine_message=engine.engine_message,
        uptime_seconds=round(time.monotonic() - _start_time, 3),
    )
