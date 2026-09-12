"""Explicit consent tracking ORM model.

Every health-data permission grant/denial and revocation is recorded so the
product can prove "explicit consent" and let users audit their choices.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin

CONSENT_DATA_TYPES = ("steps", "sleep", "activity", "screen_time", "demographic_optional")


class ConsentRecord(Base, TimestampMixin):
    __tablename__ = "consent_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    data_type: Mapped[str] = mapped_column(String(40), nullable=False)
    consent_given: Mapped[bool] = mapped_column(Boolean, nullable=False)
    # Explicit "I revoked it" marker; for display a user may still have granted
    # a device permission while revoking app-level consent.
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    Index("ix_consent_user_type", "user_id", "data_type")