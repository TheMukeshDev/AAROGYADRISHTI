"""Personal learning profile ORM models (Phase 5).

A ``PersonalLearning`` aggregates the observations a user has accumulated about
one specific relationship (``pattern_type`` + ``intervention``), e.g.
"longer sleep" (intervention) and "next-day energy" (pattern). The individual
experiments it is based on are snapshotted as ``PersonalLearningEvidence``
rows so the profile can be recalculated without losing per-experiment detail.

These rows are always phrased as observations:
``causality_proven`` defaults to False and no column stores a medical claim.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class PersonalLearning(Base, TimestampMixin):
    __tablename__ = "personal_learnings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    # Relationship this learning describes.
    pattern_type: Mapped[str] = mapped_column(String(60), nullable=False)
    intervention: Mapped[str] = mapped_column(String(120), nullable=False)
    # The metric on which the observation is strongest (largest |change|).
    target_metric: Mapped[str | None] = mapped_column(String(40), nullable=True)
    # proposed (no user confirmation yet) | confirmed | dismissed.
    state: Mapped[str] = mapped_column(String(20), nullable=False, default="proposed")
    evidence_level: Mapped[str] = mapped_column(String(40), nullable=False, server_default="INSUFFICIENT")
    # positive | negative | mixed | neutral | insufficient
    evidence_state: Mapped[str] = mapped_column(String(20), nullable=False, server_default="insufficient")
    consistency_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    hypothesis: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    causality_proven: Mapped[bool] = mapped_column(default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "pattern_type", "intervention", name="uq_personal_learning_key"),
        Index("ix_personal_learning_user_state", "user_id", "state"),
    )


class PersonalLearningEvidence(Base, TimestampMixin):
    """One experiment folded into a learning - an immutable snapshot."""

    __tablename__ = "personal_learning_evidence"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    learning_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("personal_learnings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    experiment_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # candidate | accepted - which candidate state produced this snapshot.
    source: Mapped[str] = mapped_column(String(20), nullable=False, server_default="candidate")
    evidence_level: Mapped[str] = mapped_column(String(40), nullable=False, server_default="INSUFFICIENT")
    direction: Mapped[str] = mapped_column(String(12), nullable=False, server_default="no_change")  # improved|worsened|no_change
    effect_magnitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    data_completeness: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_adherence: Mapped[float | None] = mapped_column(Float, nullable=True)
    observed_change: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_ple_learning_id", "learning_id"),
    )