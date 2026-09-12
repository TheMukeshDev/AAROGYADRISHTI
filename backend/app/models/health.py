"""Health source connections and synced health data ORM models."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class HealthConnection(Base, TimestampMixin):
    """A device/platform a user has granted access to (e.g. Health Connect)."""

    __tablename__ = "health_connections"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(nullable=False)  # health_connect | manual

    steps_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sleep_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    activity_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    connected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_health_connections_user_provider"),
        Index("ix_health_connections_user", "user_id"),
    )


class DailyHealthData(Base, TimestampMixin):
    """Raw synced readings for a single day, keyed by provider source.

    These rows are *observations* pulled from a device; they are never merged
    with manually entered values, and the ``source`` is always recorded so
    Phase 2 analytics can reason about provenance and quality.
    """

    __tablename__ = "daily_health_data"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    source: Mapped[str] = mapped_column(nullable=False)  # health_connect

    steps: Mapped[int | None] = mapped_column(nullable=True)
    active_minutes: Mapped[int | None] = mapped_column(nullable=True)
    sleep_minutes: Mapped[int | None] = mapped_column(nullable=True)

    # The device sync event that produced this row (dedup point).
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "date", "source", name="uq_daily_health_user_date_source"),
        Index("ix_daily_health_user_date", "user_id", "date"),
    )