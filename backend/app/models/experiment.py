"""Personal Experiment Engine ORM models (Phase 3).

Every experiment belongs to exactly one user (``experiments.user_id``) and is
isolated by user_id on every query. JSON columns store structured snapshots:
metric values, differences and the "learning" block that a future phase can
consume. We never store medical conclusions - only observations.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin

EXPERIMENT_STATUSES = ("recommended", "active", "completed", "cancelled", "paused")


class Experiment(Base, TimestampMixin):
    """A 7-day lifestyle experiment started from a detected personal pattern."""

    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Identifies the Phase 2 pattern this experiment was built from
    # (e.g. "sleep_energy"). Stored as a snapshot - never a live FK to a
    # patterns table, because patterns are recomputed per-run.
    pattern_id: Mapped[str | None] = mapped_column(String(60), nullable=True)
    # experiment_type references the matching ExperimentTemplate row
    # (e.g. "sleep_consistency").
    experiment_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(160), nullable=False)
    hypothesis: Mapped[str] = mapped_column(Text, nullable=False)
    intervention: Mapped[str] = mapped_column(Text, nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", index=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_experiments_user_status", "user_id", "status"),
    )


class ExperimentTemplate(Base, TimestampMixin):
    """A predefined, conservative wellness intervention template (Phase 3, section 2)."""

    __tablename__ = "experiment_templates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    experiment_type: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    hypothesis_template: Mapped[str] = mapped_column(Text, nullable=False)
    intervention: Mapped[str] = mapped_column(Text, nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    # Metric names tracked by this experiment (subset of daily-log fields).
    required_metrics: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ExperimentDailyLog(Base, TimestampMixin):
    """A single day's progress record inside an active experiment.

    Metric VALUES are stored on the user's existing ``daily_logs`` row for that
    date (Phase 3 reuses the Phase 1 daily-log system); this row records the
    experiment-specific bookkeeping: was the day completed, was the intervention
    target met, and optional free-text notes. Missing values stay NULL.
    """

    __tablename__ = "experiment_daily_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    experiment_id: Mapped[int] = mapped_column(
        ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    target_met: Mapped[bool | None] = mapped_column(nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # day number within the experiment window (1..duration_days) for progress UI
    day_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        UniqueConstraint("experiment_id", "date", name="uq_experiment_daily_logs_exp_date"),
    )


class ExperimentResult(Base, TimestampMixin):
    """Structured before/after comparison for a completed experiment."""

    __tablename__ = "experiment_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    experiment_id: Mapped[int] = mapped_column(
        ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    baseline_values: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    experiment_values: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    differences: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    effect_direction: Mapped[str | None] = mapped_column(String(20), nullable=True)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confidence_level: Mapped[str] = mapped_column(String(30), nullable=False, default="insufficient_data")
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    limitations: Mapped[str] = mapped_column(Text, nullable=False, default="")
    learning: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)