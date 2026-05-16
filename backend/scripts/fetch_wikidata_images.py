"""
fetch_wikidata_images.py — OPTIONAL polish.

Fetches player photos and team logos from Wikidata / Wikimedia Commons and
writes them under backend/app/static/{players,teams}/. The web app works
fully WITHOUT this — PlayerAvatar falls back to deterministic initials when
files are missing.

Expected runtime: ~30–45 minutes for the full ~2,200-player dataset.
Coverage seen in practice: ~70% players, ~95% teams. Resumable — existing
files are skipped, so re-running fills gaps without re-downloading.

Usage:
    pip install -r backend/requirements-scripts.txt
    python backend/scripts/fetch_wikidata_images.py [--limit N] [--teams-only] [--players-only]

Rate limit: 1 request/second to Wikidata (be a good citizen — the SPARQL
endpoint is free).
"""
from __future__ import annotations

import argparse
import io
import json
import logging
import re
import sys
import time
from pathlib import Path
from typing import Iterable

import requests
from PIL import Image
from tqdm import tqdm

# Resolve project paths the same way the engine does.
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
METADATA_PATH = PROJECT_ROOT / "models" / "gp2" / "player_metadata_v2.json"
PLAYERS_OUT = BACKEND_DIR / "app" / "static" / "players"
TEAMS_OUT = BACKEND_DIR / "app" / "static" / "teams"

WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
WIKIMEDIA_FILE = "https://commons.wikimedia.org/wiki/Special:FilePath/{name}"
USER_AGENT = (
    "ReplacementScoutBot/0.1 (https://github.com/mugalal/football-player-replacement; "
    "academic/portfolio use)"
)
RATE_LIMIT_SECONDS = 1.0
PLAYER_SIZE = (200, 200)
LOGO_MAX_SIZE = (256, 256)
JPEG_QUALITY = 85
IMAGE_DOWNLOAD_DEADLINE_SECONDS = 45

# Q937857 = association football player.
PLAYER_SPARQL = """
SELECT ?item ?image WHERE {{
  ?item wdt:P106 wd:Q937857 .
  ?item wdt:P18 ?image .
  {{ ?item rdfs:label "{name}"@en . }}
  UNION
  {{ ?item skos:altLabel "{name}"@en . }}
}}
LIMIT 10
""".strip()

# Q476028 = association football club.
CLUB_SPARQL = """
SELECT ?item ?logo WHERE {{
  ?item wdt:P31/wdt:P279* wd:Q476028 .
  ?item wdt:P154 ?logo .
  {{ ?item rdfs:label "{name}"@en . }}
  UNION
  {{ ?item skos:altLabel "{name}"@en . }}
  UNION
  {{
    ?item rdfs:label ?label .
    FILTER(LANG(?label) = "en")
    FILTER(CONTAINS(LCASE(STR(?label)), LCASE("{name}")))
  }}
}}
LIMIT 10
""".strip()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("fetch-images")

_SLUG_NON_ALNUM = re.compile(r"[^a-z0-9]+")
def team_slug(name: str) -> str:
    return _SLUG_NON_ALNUM.sub("-", name.lower()).strip("-") or "unknown"


def sparql(query: str, attempt: int = 0) -> list[dict]:
    """Call Wikidata SPARQL endpoint with exponential backoff on 429/5xx."""
    try:
        r = requests.get(
            WIKIDATA_SPARQL,
            params={"query": query, "format": "json"},
            headers={"User-Agent": USER_AGENT, "Accept": "application/sparql-results+json"},
            timeout=30,
        )
    except requests.RequestException as e:
        log.warning("SPARQL network error: %s", e)
        if attempt < 4:
            time.sleep(2 ** attempt)
            return sparql(query, attempt + 1)
        return []

    if r.status_code in (429, 500, 502, 503, 504):
        if attempt < 4:
            wait = 2 ** attempt
            log.warning("SPARQL %d, backing off %ss", r.status_code, wait)
            time.sleep(wait)
            return sparql(query, attempt + 1)
        return []
    if not r.ok:
        return []
    return r.json().get("results", {}).get("bindings", [])


def download_image(image_url: str) -> bytes | None:
    """Wikidata P18 values look like
    'http://commons.wikimedia.org/wiki/Special:FilePath/Foo.jpg' — fetch directly."""
    image_url = image_url.replace("http://", "https://", 1)
    try:
        with requests.get(
            image_url,
            headers={"User-Agent": USER_AGENT},
            stream=True,
            timeout=(10, 15),
        ) as r:
            if not r.ok:
                return None
            chunks: list[bytes] = []
            started = time.monotonic()
            for chunk in r.iter_content(chunk_size=64 * 1024):
                if time.monotonic() - started > IMAGE_DOWNLOAD_DEADLINE_SECONDS:
                    log.warning("Image download timed out (%s)", image_url)
                    return None
                if chunk:
                    chunks.append(chunk)
            return b"".join(chunks)
    except requests.RequestException as e:
        log.warning("Image download failed (%s): %s", image_url, e)
        return None


def fetch_player_photo(name: str, out_path: Path) -> bool:
    if out_path.exists():
        return True
    rows = sparql(PLAYER_SPARQL.format(name=_escape(name)))
    time.sleep(RATE_LIMIT_SECONDS)
    image_url = next(
        (row["image"]["value"] for row in rows if "image" in row),
        None,
    )
    if not image_url:
        return False
    data = download_image(image_url)
    if not data:
        return False
    try:
        with Image.open(io.BytesIO(data)) as img:
            img = img.convert("RGB")
            img.thumbnail(PLAYER_SIZE, Image.LANCZOS)
            # Center-crop to a square for a clean avatar.
            w, h = img.size
            side = min(w, h)
            left, top = (w - side) // 2, (h - side) // 2
            img = img.crop((left, top, left + side, top + side))
            img = img.resize(PLAYER_SIZE, Image.LANCZOS)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(out_path, "JPEG", quality=JPEG_QUALITY, optimize=True)
        return True
    except Exception as e:
        log.warning("Image processing failed (%s): %s", name, e)
        return False


def fetch_team_logo(name: str, out_path: Path) -> bool:
    if out_path.exists():
        return True
    rows = sparql(CLUB_SPARQL.format(name=_escape(name)))
    time.sleep(RATE_LIMIT_SECONDS)
    image_url = next(
        (row["logo"]["value"] for row in rows if "logo" in row),
        None,
    )
    if not image_url:
        return False
    data = download_image(_commons_thumbnail_url(image_url, LOGO_MAX_SIZE[0]))
    if not data:
        return False
    try:
        with Image.open(io.BytesIO(data)) as img:
            img.thumbnail(LOGO_MAX_SIZE, Image.LANCZOS)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            # Preserve transparency for logos — save as PNG.
            if img.mode not in ("RGBA", "LA"):
                img = img.convert("RGBA")
            img.save(out_path, "PNG", optimize=True)
        return True
    except Exception as e:
        log.warning("Logo processing failed (%s): %s", name, e)
        return False


def _escape(s: str) -> str:
    # SPARQL string-literal escape — double quotes and backslashes only.
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _commons_thumbnail_url(image_url: str, width: int) -> str:
    # Special:FilePath?width=N asks Wikimedia to rasterize SVG logos to PNG.
    sep = "&" if "?" in image_url else "?"
    return f"{image_url}{sep}width={width}"


def load_metadata() -> dict[str, dict]:
    if not METADATA_PATH.exists():
        log.error("Missing %s — cannot run.", METADATA_PATH)
        sys.exit(1)
    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=None, help="Cap how many players/teams to process.")
    ap.add_argument("--start-index", type=int, default=0, help="Skip the first N players/teams before processing.")
    ap.add_argument("--players-only", action="store_true")
    ap.add_argument("--teams-only", action="store_true")
    args = ap.parse_args()

    metadata = load_metadata()
    do_players = not args.teams_only
    do_teams = not args.players_only

    if do_players:
        players: Iterable[tuple[str, str]] = (
            (pid, m.get("name", "")) for pid, m in metadata.items() if m.get("name")
        )
        players = list(players)
        if args.start_index:
            players = players[args.start_index :]
        if args.limit is not None:
            players = players[: args.limit]
        log.info("Fetching photos for %d players → %s", len(players), PLAYERS_OUT)
        ok = 0
        for pid, name in tqdm(players, desc="players"):
            if fetch_player_photo(name, PLAYERS_OUT / f"{pid}.jpg"):
                ok += 1
        log.info("Players: %d/%d (%.0f%%)", ok, len(players), 100 * ok / max(1, len(players)))

    if do_teams:
        team_names = sorted({m.get("team", "") for m in metadata.values() if m.get("team")})
        if args.start_index:
            team_names = team_names[args.start_index :]
        if args.limit is not None:
            team_names = team_names[: args.limit]
        log.info("Fetching logos for %d teams → %s", len(team_names), TEAMS_OUT)
        ok = 0
        for name in tqdm(team_names, desc="teams"):
            if fetch_team_logo(name, TEAMS_OUT / f"{team_slug(name)}.png"):
                ok += 1
        log.info("Teams: %d/%d (%.0f%%)", ok, len(team_names), 100 * ok / max(1, len(team_names)))


if __name__ == "__main__":
    main()
