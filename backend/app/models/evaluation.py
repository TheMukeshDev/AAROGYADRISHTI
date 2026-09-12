"""Experiment evaluation ORM models (Phase 4).

``experiment_results`` holds the human-facing comparison (Phase 3);
``experiment_metric_results`` / ``experiment_evidence`` hold the auditable
numeric evaluation (Phase 4); ``learning_candidates`` are the bridge into the
Phase 5 personal learning profile. ``causality_proven`` is always FALSE in this
product version - these are personal observations, never causal proof.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Boolean, Date, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin

LEARNING_CANDIDATE_STATUSES = ("candidate", "accepted", "rejected", "superseded")


class ExperimentMetricResult(Base, TimestampMixin):
    """Per-metric baseline vs experiment statistics (Phase 4, section 15)."""

    __tablename__ = "experiment_metric_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    experiment_id: Mapped[int] = mapped_column(
        ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    metric_name: Mapped[str] = mapped_column(String(40), nullable=False)
    baseline_mean: Mapped[float | None] = mapped_column(Float, nullable=True)
    experiment_mean: Mapped[float | None] = mapped_column(Float, nullable=True)
    difference: Mapped[float | None] = mapped_column(Float, nullable=True)
    percentage_change: Mapped[float | None] = mapped_column(Float, nullable=True)
    baseline_median: Mapped[float | None] = mapped_column(Float, nullable=True)
    experiment_median: Mapped[float | None] = mapped_column(Float, nullable=True)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    valid_observations: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    direction: Mapped[str] = mapped_column(String(20), nullable=False, default="no_change")

    __table_args__ = (Index("ix_experiment_metric_results_exp", "experiment_id"),)


class ExperimentEvidence(Base, TimestampMixin):
    """Evidence assessment for a completed experiment (Phase 4, section 15)."""

    __tablename__ = "experiment_evidence"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    experiment_id: Mapped[int] = mapped_column(
        ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    data_completeness: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    target_adherence: Mapped[float | None] = mapped_column(Float, nullable=True)
    consistency_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    evidence_level: Mapped[str] = mapped_column(String(40), nullable=False, default="INSUFFICIENT")
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    limitations: Mapped[str] = mapped_column(Text, nullable=False, default="")
    causality_proven: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class LearningCandidate(Base, TimestampMixin):
    """A structured 'personal learning candidate' ready for Phase 5 aggregation.

    It is an OBSERVATION, not a fact. It stays a candidate until repeated
    evidence is aggregated by the Personal Learning profile.
    """

    __tablename__ = "learning_candidates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    experiment_id: Mapped[int] = mapped_column(
        ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    pattern_type: Mapped[str] = mapped_column(String(60), nullable=False)
    intervention: Mapped[str] = mapped_column(String(60), nullable=False)
    observed_change: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    evidence_level: Mapped[str] = mapped_column(String(40), nullable=False, default="EARLY_OBSERVATION")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="candidate")
    causality_proven: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (Index("ix_learning_candidates_user_status", "user_id", "status"),)