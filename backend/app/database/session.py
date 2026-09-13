"""Database engine and session lifecycle (SQLAlchemy 2.0 style)."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import Engine, StaticPool, create_engine, event, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.core.logging import get_logger

_settings = get_settings()

if _settings.is_sqlite:
    # SQLite (used by tests and quick local runs) needs single-thread pooling
    # and foreign-key enforcement per-connection. StaticPool keeps a single
    # shared in-memory database across all connections.
    engine: Engine = create_engine(
        _settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=_settings.db_echo,
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _record):  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    engine = create_engine(
        _settings.database_url,
        pool_size=_settings.db_pool_size,
        max_overflow=_settings.db_max_overflow,
        pool_pre_ping=True,
        echo=_settings.db_echo,
    )

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a request-scoped database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def db_is_reachable(db: Session) -> bool:
    """Return True when a trivial read succeeds.

    Used by the database health check. Only the exception type is logged so
    driver details and connection strings never reach the logs.
    """
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        get_logger(__name__).warning("Database reachability check failed: %s", type(exc).__name__)
        return False
    return True