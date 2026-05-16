"""
Engine wrapper.

Imports the locked GP2 scouting engine via sys.path and exposes a single
async entry point `run_engine(fn, *args, **kwargs)` that routes every
CPU-bound engine call through a shared single-worker ThreadPoolExecutor.

The single-worker constraint is structural concurrency control: it means we
can never run two model inferences in parallel, regardless of which endpoint
triggered them. The /api/search job queue's "1 running + 3 pending" policy
is layered on top for upgrade jobs specifically.
"""
from __future__ import annotations

import asyncio
import logging
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

from app.config import PROJECT_ROOT

logger = logging.getLogger(__name__)

# Make `from src.gp2.evaluation import scouting_engine` resolvable.
_project_root_str = str(PROJECT_ROOT)
if _project_root_str not in sys.path:
    sys.path.insert(0, _project_root_str)

# State exposed to the rest of the app.
engine_state: str = "warming"      # "warming" | "ready" | "unavailable"
engine_message: str | None = None

# Import the engine lazily-friendly: we still import at module load so the
# rest of the app can reference `scouting_engine.*` directly, but if the
# import itself fails we mark the engine unavailable and re-raise so the
# caller sees a clean error.
try:
    from src.gp2.evaluation import scouting_engine  # type: ignore
except Exception as e:  # pragma: no cover — only fires if src/ is missing
    scouting_engine = None  # type: ignore[assignment]
    engine_state = "unavailable"
    engine_message = f"Engine import failed: {e}"
    logger.error("Engine import failed:\n%s", traceback.format_exc())


# Shared single-worker executor. Lazily (re)created so that a shutdown
# during one app lifespan doesn't permanently kill the executor for a
# subsequent lifespan in the same process — important for pytest's
# TestClient pattern, where each test may open a fresh TestClient.
_executor: ThreadPoolExecutor | None = None


def _ensure_executor() -> ThreadPoolExecutor:
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="engine")
    return _executor


def engine_loaded() -> bool:
    return engine_state == "ready"


def set_state(state: str, message: str | None = None) -> None:
    global engine_state, engine_message
    engine_state = state
    engine_message = message


async def run_engine(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Run a CPU-bound engine function on the shared single-worker executor."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_ensure_executor(), lambda: fn(*args, **kwargs))


def shutdown_executor() -> None:
    """Stop the executor. Safe to call multiple times; a later run_engine
    call will lazily create a fresh executor."""
    global _executor
    if _executor is not None:
        _executor.shutdown(wait=False, cancel_futures=False)
        _executor = None
