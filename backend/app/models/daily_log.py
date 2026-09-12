"""Daily lifestyle check-in ORM model.

Design rule (Phase 1): we NEVER fabricate missing data. Columns whose value is
not known are stored as ``NULL`` rather than ``0`` so downstream analytics can
distinguish "measured zero" from "not collected".
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class DailyLog(Base, TimestampMixin):
    __tablename__ = "daily_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)

    # --- Sleep ---------------------------------------------------------------
    sleep_hours: Mapped[float | None] = mapped_column(nullable=True)
    sleep_quality: Mapped[str | None] = mapped_column(nullable=True)  # good | fair | poor

    # --- Activity ------------------------------------------------------------
    steps: Mapped[int | None] = mapped_column(nullable=True)
    active_minutes: Mapped[int | None] = mapped_column(nullable=True)
    exercise_minutes: Mapped[int | None] = mapped_column(nullable=True)
    # exercise_level: none | light | moderate | intense (from check-in quick picker)
    exercise_level: Mapped[str | None] = mapped_column(nullable=True)

    # --- Diet / hydration ----------------------------------------------------
    water_liters: Mapped[float | None] = mapped_column(nullable=True)
    meal_quality: Mapped[str | None] = mapped_column(nullable=True)  # healthy | mixed | processed

    # --- Device / screens ----------------------------------------------------
    screen_time_minutes: Mapped[int | None] = mapped_column(nullable=True)
    late_night_screen: Mapped[bool | None] = mapped_column(nullable=True)

    # --- Substances ----------------------------------------------------------
    caffeine: Mapped[str | None] = mapped_column(nullable=True)  # none | low | moderate | high

    # --- Subjective wellbeing ------------------------------------------------
    mood: Mapped[str | None] = mapped_column(nullable=True)  # very_low|low|okay|good|great
    energy: Mapped[int | None] = mapped_column(nullable=True)  # 1..10
    stress: Mapped[int | None] = mapped_column(nullable=True)  # 1..5

    # How this log was created (manual | health_sync | demo)
    source: Mapped[str] = mapped_column(nullable=False, default="manual")

    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_daily_logs_user_date"),
        Index("ix_daily_logs_user_date", "user_id", "date"),
        Index("ix_daily_logs_user_created", "user_id", "created_at"),
    )