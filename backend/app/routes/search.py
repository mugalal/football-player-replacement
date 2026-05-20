"""
POST /api/search — synchronous if no upgrades, otherwise enqueued as an async job.
GET  /api/search/{job_id} — model-independent job-state lookup.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.deps import require_engine
from app.schemas.search import (
    JobAcceptedResponse,
    JobRecord,
    SearchRequest,
    SyncSearchResponse,
)
from app.services import engine
from app.services.images import enrich_search_result
from app.services.jobs import RETRY_AFTER_SECONDS, store

logger = logging.getLogger(__name__)

router = APIRouter()


def _has_upgrades(req: SearchRequest) -> bool:
    if req.upgrades is None:
        return False
    if isinstance(req.upgrades, (list, dict)) and len(req.upgrades) == 0:
        return False
    return True


@router.post("/search")
async def post_search(
    req: SearchRequest,
    response: Response,
    request: Request,
    _: None = Depends(require_engine),
):
    kwargs = dict(
        sources=req.sources,
        upgrades=req.upgrades if req.upgrades is not None else [],
        upgrade_intensity=req.upgrade_intensity,
        top_k=req.top_k,
        filters=req.filters,
        exclude_sources=req.exclude_sources,
        seed=req.seed,
    )

    if not _has_upgrades(req):
        # Fast path: similarity-only search runs in well under a second.
        try:
            result = await engine.run_engine(
                engine.scouting_engine.search_replacements, **kwargs
            )
        except ValueError as e:
            raise HTTPException(400, detail=str(e))
        except Exception as e:
            logger.exception("sync search failed")
            raise HTTPException(500, detail=str(e))
        # Attach photo_url + team_logo_url to sources and candidates.
        return SyncSearchResponse(**enrich_search_result(result, request))

    # Upgrade path: enqueue as a background job.
    job_id = store.enqueue(kwargs)
    if job_id is None:
        response.headers["Retry-After"] = str(RETRY_AFTER_SECONDS)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Search queue full, retry shortly",
            headers={
                "Retry-After": str(RETRY_AFTER_SECONDS),
            },
        )
    return JobAcceptedResponse(job_id=job_id, status="pending")


@router.get("/search/{job_id}", response_model=JobRecord)
def get_job(job_id: str, request: Request) -> JobRecord:
    # Model-independent: only reads the in-memory job store.
    record = store.get(job_id)
    if record is None:
        raise HTTPException(404, detail=f"Job not found: {job_id}")
    # If the job is done, enrich its result with per-request image URLs.
    if record.get("status") == "done" and record.get("result"):
        record = {
            **record,
            "result": enrich_search_result(record["result"], request),
        }
    return JobRecord(**record)
