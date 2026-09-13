"""AarogyaDrishti API - FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api import auth, coach, consent, daily_logs, dashboard, experiments, health, learning, profile
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware, SecurityHeadersMiddleware
from app.core.rate_limit import RateLimitMiddleware

settings = get_settings()
configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Seed predefined experiment templates on startup (idempotent)."""
    from app.database.session import SessionLocal
    from app.services.experiment_templates import seed_experiment_templates

    db = SessionLocal()
    try:
        seed_experiment_templates(db)
    except Exception:  # pragma: no cover - startup must not crash on seed issues
        db.rollback()
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "AarogyaDrishti - 'See Your Habits. Shape Your Health.' "
        "A personalized lifestyle observation system (data collection, pattern "
        "detection, experiments, evaluation, personal learning, AI coach). "
        "It does not diagnose, treat or predict disease."
    ),
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# --- Middleware ---------------------------------------------------------------
# Order matters. add_middleware wraps the previous stack, so the LAST middleware
# added is the OUTERMOST. Request flow (outermost -> innermost):
#   SecurityHeaders -> CORS -> RateLimit -> RequestContext -> GZip
# Security headers are outermost so even rate-limited/error responses get them;
# CORS sits in front of the rate limiter so browser preflights are not blocked.
app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)

# --- Routers ----------------------------------------------------------------
for router in (
    auth.router,
    profile.router,
    daily_logs.router,
    dashboard.router,
    health.router,
    consent.router,
    experiments.router,
    learning.router,
    coach.router,
):
    app.include_router(router, prefix=settings.api_v1_prefix)

register_exception_handlers(app)


@app.get("/health", tags=["health"])
def healthcheck() -> dict:
    """Liveness probe - does not touch the database."""
    return {"status": "ok", "app": settings.app_name, "phase": "1-6"}