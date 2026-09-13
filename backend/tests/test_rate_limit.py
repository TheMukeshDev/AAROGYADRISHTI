"""Rate limiter tests (unit + middleware wiring)."""

from __future__ import annotations

import time

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.rate_limit import RateLimiter, RateLimits, RateLimitMiddleware
from app.core.errors import CODE_RATE_LIMITED


def test_limiter_allows_under_limit_and_blocks_over():
    limiter = RateLimiter(RateLimits(enabled=True, general_per_minute=3, auth_per_minute=1))
    assert limiter.is_limited("1.2.3.4", 3) is False
    assert limiter.is_limited("1.2.3.4", 3) is False
    assert limiter.is_limited("1.2.3.4", 3) is False
    assert limiter.is_limited("1.2.3.4", 3) is True
    # A different client has its own fresh budget.
    assert limiter.is_limited("5.6.7.8", 3) is False


def test_limiter_window_resets():
    limiter = RateLimiter(RateLimits(enabled=True, general_per_minute=1, auth_per_minute=1))
    assert limiter.is_limited("9.9.9.9", 1) is False
    assert limiter.is_limited("9.9.9.9", 1) is True
    # Simulate the next minute passing; the budget must be restored.
    limiter._buckets["9.9.9.9"].window_started = time.monotonic() - 61.0
    assert limiter.is_limited("9.9.9.9", 1) is False


def test_limit_for_path_picks_auth_window():
    limits = RateLimits(enabled=True, general_per_minute=5, auth_per_minute=2)
    assert RateLimiter.limit_for("/api/v1/auth/login", limits) == 2
    assert RateLimiter.limit_for("/api/v1/auth/register", limits) == 2
    assert RateLimiter.limit_for("/api/v1/daily-logs", limits) == 5
    assert RateLimiter.limit_for("/health", limits) == 5


def test_middleware_returns_429_with_error_envelope():
    app = FastAPI()

    @app.get("/probe")
    def probe():
        return {"ok": True}

    app.add_middleware(
        RateLimitMiddleware,
        limits=RateLimits(enabled=True, general_per_minute=1, auth_per_minute=1),
    )

    with TestClient(app, raise_server_exceptions=False) as client:
        first = client.get("/probe")
        assert first.status_code == 200

        second = client.get("/probe")
        assert second.status_code == 429
        body = second.json()
        assert body["error"]["code"] == CODE_RATE_LIMITED
        assert second.headers["Retry-After"] == "60"


def test_middleware_is_bypassed_when_disabled():
    app = FastAPI()

    @app.get("/probe")
    def probe():
        return {"ok": True}

    app.add_middleware(
        RateLimitMiddleware,
        limits=RateLimits(enabled=False, general_per_minute=1, auth_per_minute=1),
    )

    with TestClient(app, raise_server_exceptions=False) as client:
        for _ in range(5):
            assert client.get("/probe").status_code == 200