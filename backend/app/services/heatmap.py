"""
Heatmap aggregation service.

Streams `models/gp2/player_match_docs_split.jsonl` and counts pitch-zone
occurrences per player. The engine's tokens encode locations as zone IDs
on a 6×3 grid (NUM_X_BINS=6, NUM_Y_BINS=3, row-major from top-left of a
120×80 StatsBomb pitch — see src/gp2/preprocess/zones.py).

Token shapes we extract zones from:
  pass|z17_z11|f|r|l|med    -> 17 (start zone)
  carry|z16_z17|fwd         -> 16
  shot|z11|on|r|open|xg_l|mid -> 11
  pressure|z16|reg          -> 16
  duel|z14|ground|lost      -> 14
  ... etc.

Tokens that are pure modifiers (e.g. `progressive_pass`, `cut_inside_right`,
`under_pressure`) have no zone field and are skipped.

We use *start zone only*, which represents "where this player was active."
This is the right primitive for "show me their pitch footprint." We also
keep the totals so the heatmap can be normalized to percentages downstream.

The data file is ~132 MB and contains ~49k player-match documents — a full
scan takes a few seconds. The result for each player is cached in
process memory; the index `_zone_index` (built lazily on first call) maps
player_id -> 18-element count array.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Iterable, Optional

from app.config import PROJECT_ROOT

logger = logging.getLogger(__name__)

# Matches `z<digits>` at the start of the second pipe-field, possibly followed
# by `_z<digits>` (start_end pair) or other field separators. We only care
# about the first (start) zone.
_ZONE_RE = re.compile(r"^z(\d+)")

NUM_ZONES = 18  # 6×3 grid
DOCS_PATH = PROJECT_ROOT / "models" / "gp2" / "player_match_docs_split.jsonl"

# player_id -> [count_z0, count_z1, ..., count_z17]
_zone_index: Optional[dict[str, list[int]]] = None
_index_lock = asyncio.Lock()


def _extract_zone(token: str) -> Optional[int]:
    """Return the start-zone id (0-17) for a structured token, or None for modifier-only tokens."""
    # Tokens look like "<verb>|<zone-or-pair>|<...>" — split once, look at field[1].
    parts = token.split("|", 2)
    if len(parts) < 2:
        return None
    m = _ZONE_RE.match(parts[1])
    if not m:
        return None
    try:
        zid = int(m.group(1))
    except ValueError:
        return None
    if 0 <= zid < NUM_ZONES:
        return zid
    return None


def _build_index_sync() -> dict[str, list[int]]:
    """Stream the docs jsonl once and tally zones per player. Blocking I/O — caller must offload."""
    if not DOCS_PATH.exists():
        raise FileNotFoundError(f"{DOCS_PATH} not found")

    index: dict[str, list[int]] = {}
    n_docs = 0
    with open(DOCS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                doc = json.loads(line)
            except json.JSONDecodeError:
                continue
            pid = doc.get("player_id")
            if pid is None:
                continue
            pid = str(pid)
            counts = index.get(pid)
            if counts is None:
                counts = [0] * NUM_ZONES
                index[pid] = counts
            for tok in doc.get("onball_tokens", []) or []:
                z = _extract_zone(tok)
                if z is not None:
                    counts[z] += 1
            for tok in doc.get("offball_tokens", []) or []:
                z = _extract_zone(tok)
                if z is not None:
                    counts[z] += 1
            n_docs += 1
    logger.info("Heatmap index built: %d players from %d documents", len(index), n_docs)
    return index


async def _ensure_index() -> dict[str, list[int]]:
    global _zone_index
    if _zone_index is not None:
        return _zone_index
    async with _index_lock:
        if _zone_index is not None:
            return _zone_index
        loop = asyncio.get_running_loop()
        _zone_index = await loop.run_in_executor(None, _build_index_sync)
        return _zone_index


async def player_heatmap(player_id: str) -> Optional[list[int]]:
    """Return the 18-element zone-count array for a player, or None if unknown."""
    idx = await _ensure_index()
    counts = idx.get(str(player_id))
    if counts is None:
        return None
    return list(counts)


async def aggregate_heatmap(player_ids: Iterable[str]) -> list[int]:
    """Sum zone counts across a set of player_ids. Missing IDs contribute zeros."""
    idx = await _ensure_index()
    out = [0] * NUM_ZONES
    for pid in player_ids:
        counts = idx.get(str(pid))
        if counts is None:
            continue
        for i, c in enumerate(counts):
            out[i] += c
    return out
