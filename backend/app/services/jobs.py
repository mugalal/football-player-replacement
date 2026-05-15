"""
In-memory async job store for upgrade searches.

Design:
  - One asyncio.Queue (maxsize=3) of pending job_ids.
  - One long-running worker task drains it; each job runs through
    services.engine.run_engine(...), which uses the shared single-worker
    executor — so heavy work is automatically serialized with any other
    engine call site (validation endpoint, similar-players, etc.).
  - Records live in a dict keyed by job_id. Records older than 1 hour are
    swept on every enqueue and every status lookup.

Lost on restart by design. Acceptable for v1; a Redis/SQLite store is the
follow-up if production reliability is needed.
"""
from __future__ import annotations

import asyncio
import logging
import traceback
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from app.services import engine

logger = logging.getLogger(__name__)

JOB_TTL = timedelta(hours=1)
QUEUE_MAXSIZE = 3
RETRY_AFTER_SECONDS = 30


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Job:
    job_id: str
    status: str  # "pending" | "running" | "done" | "error"
    created_at: str
    updated_at: str
    kwargs: dict[str, Any]
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        # kwargs is internal — never expose it
        return {
            "job_id": self.job_id,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "result": self.result,
            "error": self.error,
        }


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._queue: asyncio.Queue[str] = asyncio.Queue(maxsize=QUEUE_MAXSIZE)
        self._worker_task: asyncio.Task | None = None
        self._running_job_id: str | None = None

    def _sweep(self) -> None:
        cutoff = datetime.now(timezone.utc) - JOB_TTL
        stale = [
            jid for jid, j in self._jobs.items()
            if datetime.fromisoformat(j.created_at) < cutoff
        ]
        for jid in stale:
            del self._jobs[jid]

    def is_full(self) -> bool:
        # "Full" = there is currently a running job AND the pending queue is at capacity.
        return self._running_job_id is not None and self._queue.full()

    def enqueue(self, kwargs: dict[str, Any]) -> str | None:
        """Enqueue a job. Returns job_id, or None if capacity is exceeded."""
        self._sweep()
        if self.is_full():
            return None
        job_id = uuid.uuid4().hex
        now = _now_iso()
        self._jobs[job_id] = Job(
            job_id=job_id,
            status="pending",
            created_at=now,
            updated_at=now,
            kwargs=kwargs,
        )
        try:
            self._queue.put_nowait(job_id)
        except asyncio.QueueFull:
            # Shouldn't happen given the is_full() guard, but be defensive.
            del self._jobs[job_id]
            return None
        return job_id

    def get(self, job_id: str) -> dict[str, Any] | None:
        self._sweep()
        job = self._jobs.get(job_id)
        return job.to_dict() if job else None

    async def _worker(self) -> None:
        from app.services.engine import scouting_engine  # late import; may be None

        while True:
            try:
                job_id = await self._queue.get()
            except asyncio.CancelledError:
                return
            job = self._jobs.get(job_id)
            if job is None:
                continue
            self._running_job_id = job_id
            job.status = "running"
            job.updated_at = _now_iso()
            try:
                if scouting_engine is None:
                    raise RuntimeError("Engine unavailable")
                result = await engine.run_engine(
                    scouting_engine.search_replacements, **job.kwargs
                )
                job.result = result
                job.status = "done"
            except Exception as e:
                logger.error("Job %s failed:\n%s", job_id, traceback.format_exc())
                job.error = f"{type(e).__name__}: {e}"
                job.status = "error"
            finally:
                job.updated_at = _now_iso()
                self._running_job_id = None

    def start(self, loop: asyncio.AbstractEventLoop | None = None) -> None:
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._worker(), name="job-worker")

    async def stop(self) -> None:
        if self._worker_task is not None:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except (asyncio.CancelledError, Exception):
                pass
            self._worker_task = None


# Module-level singleton; the FastAPI app touches this via `from app.services.jobs import store`.
store = JobStore()
