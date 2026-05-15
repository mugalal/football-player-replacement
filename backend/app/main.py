"""FastAPI application entry point."""
from __future__ import annotations

import logging
import time
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import CORS_ORIGIN_REGEX, STATIC_DIR, cors_origins
from app.routes import catalog, health, players, search, validations
from app.services import engine
from app.services.jobs import store

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    start = time.monotonic()
    health._set_start_time(start)
    logger.info("Starting up. Project root: %s", engine.PROJECT_ROOT if hasattr(engine, "PROJECT_ROOT") else "(unknown)")

    # If the engine module itself failed to import, leave state as "unavailable"
    # and skip warm-up. App still serves /api/health and /api/upgrades, /api/filters.
    if engine.scouting_engine is None:
        logger.warning("Engine module did not import; serving in degraded mode.")
    else:
        try:
            await engine.run_engine(engine.scouting_engine.list_available_players, "", 1)
            engine.set_state("ready")
            elapsed = time.monotonic() - start
            logger.info("Engine ready (warm-up %.2fs)", elapsed)
        except Exception as e:
            logger.error("Engine warm-up failed:\n%s", traceback.format_exc())
            engine.set_state("unavailable", str(e))

    store.start()

    try:
        yield
    finally:
        logger.info("Shutting down.")
        await store.stop()
        engine.shutdown_executor()


app = FastAPI(
    title="Replacement Scout API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_origin_regex=CORS_ORIGIN_REGEX,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static images (player photos, team logos). Directory is auto-created on
# startup; missing individual files are handled by the URL helpers
# (services/images.py) which return None when a file is absent.
STATIC_DIR.mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "players").mkdir(exist_ok=True)
(STATIC_DIR / "teams").mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(health.router, prefix="/api")
app.include_router(catalog.router, prefix="/api")
app.include_router(players.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(validations.router, prefix="/api")
