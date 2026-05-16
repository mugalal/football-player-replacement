"""
In-memory player index with accent-insensitive substring matching.

The locked engine's `list_available_players(query, limit)` does plain
lower()+substring matching, so `q=mane` does NOT match "Sadio Mané" because
'e' != 'é'. We can't fix that in the engine (src/gp2/ is locked), so we
wrap it here:

  1. On first use, fetch the full player list once via
     `engine.list_available_players("", BIG)` (cheap — just dict
     construction over cached metadata; no model inference).
  2. Pre-compute an accent-stripped lowercased name for each player.
  3. Per request, strip accents from the user's query and substring-match
     against the pre-computed names. Return canonical (accented) entries.

Cache invalidation: none — the player set is fixed for a given model
build. If models are reloaded, the engine warmup would discard our cache
indirectly (we'd need to restart the process to rebuild it). Acceptable.
"""
from __future__ import annotations

import asyncio
import threading
import unicodedata
from typing import Any

from app.services import engine

# A bigger limit than any plausible player count; the engine returns at
# most metadata.size items regardless.
_FULL_LIST_LIMIT = 100_000

_lock = threading.Lock()
_full_list: list[dict[str, Any]] | None = None
_normalized: list[str] | None = None


def _strip_accents(s: str) -> str:
    """NFD decomposition + drop combining marks. 'Mané'→'Mane', 'Bruyne'→'Bruyne'."""
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    ).lower()


def _build_sync() -> None:
    """Synchronous (engine call) — must run on the engine executor."""
    global _full_list, _normalized
    if engine.scouting_engine is None:
        raise RuntimeError("Engine not available")
    rows = engine.scouting_engine.list_available_players("", _FULL_LIST_LIMIT)
    _full_list = rows
    _normalized = [_strip_accents(r.get("name", "")) for r in rows]


async def ensure_built() -> None:
    """Build the index if needed. Safe to call from any request handler."""
    if _full_list is not None:
        return
    # Engine call goes through the shared single-worker executor so we don't
    # block the event loop and we serialize with other engine work.
    await engine.run_engine(_acquire_and_build)


def _acquire_and_build() -> None:
    # Runs on the engine thread; the lock guards against the (unlikely)
    # case where two requests both call ensure_built() and both make it
    # past the early-return check before either has populated the cache.
    with _lock:
        if _full_list is None:
            _build_sync()


def search(query: str, limit: int) -> list[dict[str, Any]]:
    """Substring-match `query` against accent-stripped names. Caller is
    expected to have awaited `ensure_built()` first."""
    if _full_list is None or _normalized is None:
        return []
    q = _strip_accents(query).strip()
    if not q:
        return list(_full_list[:limit])
    out: list[dict[str, Any]] = []
    for row, norm in zip(_full_list, _normalized):
        if q in norm:
            out.append(row)
            if len(out) >= limit:
                break
    return out


# Test hook — lets tests reset the cache between runs without restarting
# the process.
def _reset() -> None:
    global _full_list, _normalized
    with _lock:
        _full_list = None
        _normalized = None
