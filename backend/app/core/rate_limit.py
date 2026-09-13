"""Dependency-free in-memory rate limiting.

A fixed-window counter per client key (usually the remote IP). Used to blunt
credential-stuffing and token-abuse on the authentication endpoints and to cap
runaway load from a single client. It is NOT a scalable distributed limiter -
deployments behind multiple app processes should additionally rate-limit at the
load balancer / API gateway (e.g. nginx ``limit_req``) or swap this for a
Redis-backed limiter.

A fixed window keeps the bookkeeping to a dict of (key -> window_start, count)
and is efficient enough for request rates in the low hundreds per client. The
bucket map is protected by a single lock intended for the common
single-process deployment.
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.errors import CODE_RATE_LIMITED

_WINDOW_SECONDS = 60.0

_FALLBACK_CLIENT = "unknown"

# Paths that allow unauthenticated credential brute-force / account probing.
_AUTH_PATH_SEGMENTS = ("/auth/",)


@dataclass(frozen=True)
class RateLimits:
    """Rate limit configuration for one process."""

    enabled: bool = False
    general_per_minute: int = 120
    auth_per_minute: int = 10
    trusted_proxy_count: int = 0

    @classmethod
    def from_settings(cls, settings) -> "RateLimits":  # noqa: ANN001 - avoid importing Settings to prevent cycles
        return cls(
            enabled=settings.rate_limit_enabled,
            general_per_minute=settings.rate_limit_general_per_minute,
            auth_per_minute=settings.rate_limit_auth_per_minute,
            trusted_proxy_count=settings.rate_limit_trusted_proxy_count,
        )


@dataclass
class _Bucket:
    window_started: float = 0.0
    count: int = 0


class RateLimiter:
    """Fixed-window counter, keyed by client identity."""

    def __init__(self, limits: RateLimits) -> None:
        self.limits = limits
        self._buckets: dict[str, _Bucket] = defaultdict(_Bucket)
        self._lock = Lock()

    def client_key(self, request: Request) -> str:
        """Best-effort client identity: remote IP, honoring one reverse proxy."""
        client_host = request.client.host if request.client else _FALLBACK_CLIENT
        forwarded = request.headers.get("x-forwarded-for", "")
        if self.limits.trusted_proxy_count > 0 and forwarded:
            parts = [part.strip() for part in forwarded.split(",") if part.strip()]
            if parts:
                # With N trusted proxies, the Nth value from the right is the
                # actual client; fall back to the right-most if it is missing.
                client_host = parts[-self.limits.trusted_proxy_count] or parts[-1]
        return client_host

    def is_limited(self, key: str, limit: int) -> bool:
        """Count a request for ``key`` and report whether it exceeds ``limit``."""
        now = time.monotonic()
        with self._lock:
            bucket = self._buckets[key]
            if now - bucket.window_started >= _WINDOW_SECONDS:
                bucket.window_started = now
                bucket.count = 0
            bucket.count += 1
            return bucket.count > limit

    @staticmethod
    def limit_for(path: str, limits: RateLimits) -> int:
        """Pick the appropriate per-minute budget for a request path."""
        if any(segment in path for segment in _AUTH_PATH_SEGMENTS):
            return limits.auth_per_minute
        return limits.general_per_minute


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Apply in-memory rate limits to API traffic (opt-in via ``RATE_LIMIT_ENABLED``).

    When a client exceeds its window a 429 with the standard error envelope
    (code ``rate_limited``) is returned, plus a ``Retry-After`` header.

    Order: the middleware is registered below CORS (see ``app/main.py``) so
    browser preflight requests are answered by CORS before they are counted.
    """

    def __init__(self, app, limits: RateLimits | None = None) -> None:  # noqa: ANN001
        from app.core.config import get_settings

        self._limits = limits or RateLimits.from_settings(get_settings())
        self._limiter = RateLimiter(self._limits)
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):  # noqa: ANN001
        if not self._limits.enabled:
            return await call_next(request)

        key = self._limiter.client_key(request)
        limit = self._limiter.limit_for(request.url.path, self._limits)
        if self._limiter.is_limited(key, limit):
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": CODE_RATE_LIMITED,
                        "message": "Too many requests. Please slow down and try again shortly.",
                    }
                },
                headers={"Retry-After": "60"},
            )
        return await call_next(request)