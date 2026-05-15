"""
Smoke tests — must pass with or without models/gp2/ on disk.

We use FastAPI's TestClient (synchronous, simpler than httpx.AsyncClient for
basic HTTP checks). TestClient triggers the app's lifespan when used as a
context manager, so warm-up runs but is allowed to fail without breaking
these tests — the endpoints under test are all model-independent.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_200():
    with TestClient(app) as client:
        r = client.get("/api/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert body["engine_state"] in {"warming", "ready", "unavailable"}
        assert isinstance(body["uptime_seconds"], (int, float))


def test_upgrades_returns_grouped():
    with TestClient(app) as client:
        r = client.get("/api/upgrades")
        # Model-independent: should be 200 as long as the engine module imported.
        # If src/gp2 itself failed to import (extreme case), 503 is acceptable.
        assert r.status_code in (200, 503)
        if r.status_code == 200:
            body = r.json()
            assert "onball" in body
            assert "offball" in body
            assert isinstance(body["onball"], list)
            assert isinstance(body["offball"], list)


def test_filters_has_coming_soon():
    with TestClient(app) as client:
        r = client.get("/api/filters")
        assert r.status_code in (200, 503)
        if r.status_code == 200:
            body = r.json()
            assert "coming_soon" in body
            assert isinstance(body["coming_soon"], list)
            # Specific keys we promised in the spec:
            for k in ("min_age", "max_age", "leagues", "min_market_value", "max_market_value"):
                assert k in body["coming_soon"]
