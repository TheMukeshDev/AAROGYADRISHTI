"""Request-scoped middleware.

Adds a correlation id to every request/response so a user-reported problem can
be traced in server logs without ever logging health payloads.
"""

from __future__ import annotations

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger

logger = get_logger("app.request")

REQUEST_ID_HEADER = "X-Request-ID"

# Health endpoints carry sensitive payloads - log only metadata, never bodies.
UNLOGGED_PATHS = ("/health", "/docs", "/openapi.json")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach a request id, and emit one structured access log line."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex
        request.state.request_id = request_id
        started = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - started) * 1000
            logger.exception(
                "request failed id=%s method=%s path=%s duration_ms=%.1f",
                request_id,
                request.method,
                request.url.path,
                duration_ms,
            )
            raise

        duration_ms = (time.perf_counter() - started) * 1000
        response.headers[REQUEST_ID_HEADER] = request_id
        if not request.url.path.startswith(UNLOGGED_PATHS):
            logger.info(
                "id=%s %s %s -> %s (%.1fms)",
                request_id,
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
            )
        return response
