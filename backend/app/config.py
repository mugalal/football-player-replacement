"""Backend configuration — env vars and derived paths."""
from __future__ import annotations

import os
from pathlib import Path

# Path layout: this file lives at /app/backend/app/config.py in the container,
# so parents[2] is /app — the project root that contains src/ and models/.
# Same math applies locally.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = Path(__file__).resolve().parent           # /app/backend/app
STATIC_DIR = APP_DIR / "static"                     # /app/backend/app/static
PLAYERS_STATIC_DIR = STATIC_DIR / "players"
TEAMS_STATIC_DIR = STATIC_DIR / "teams"

PORT = int(os.getenv("PORT", "7860"))

_BASE_CORS_ORIGINS = ["http://localhost:3000"]
# Permissive by design for v1: any vercel.app subdomain may call the backend.
# Tradeoff accepted because this is a portfolio/demo backend with no auth and
# no per-tenant data; locking it down requires the Vercel deployment URL to
# be known at backend deploy time, which would couple the two deploys.
CORS_ORIGIN_REGEX = r"https://.*\.vercel\.app"

def cors_origins() -> list[str]:
    extra = os.getenv("CORS_EXTRA_ORIGINS", "")
    extras = [o.strip() for o in extra.split(",") if o.strip()]
    return _BASE_CORS_ORIGINS + extras
