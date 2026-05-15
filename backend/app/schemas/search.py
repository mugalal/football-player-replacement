"""Search request/response schemas."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class SearchRequest(BaseModel):
    sources: list[str] = Field(..., min_length=1)
    upgrades: list[str] | dict[str, float] | None = None
    upgrade_intensity: float = Field(0.5, ge=0.0, le=1.0)
    top_k: int = Field(30, ge=1, le=100)
    filters: dict[str, Any] | None = None
    exclude_sources: bool = True
    seed: int = 42

    @field_validator("upgrades")
    @classmethod
    def _validate_upgrade_probs(cls, v):
        if isinstance(v, dict):
            for key, prob in v.items():
                if not isinstance(prob, (int, float)):
                    raise ValueError(f"upgrade probability for '{key}' must be numeric")
                if not (0.0 <= float(prob) <= 1.0):
                    raise ValueError(f"upgrade probability for '{key}' must be in [0.0, 1.0]")
        return v


class SyncSearchResponse(BaseModel):
    query: dict[str, Any]
    candidates: list[dict[str, Any]]
    warnings: list[str]


class JobAcceptedResponse(BaseModel):
    job_id: str
    status: Literal["pending"]


class JobRecord(BaseModel):
    job_id: str
    status: Literal["pending", "running", "done", "error"]
    created_at: str
    updated_at: str
    result: dict[str, Any] | None = None
    error: str | None = None
