"""Baseline tracking logic (Phase 1 - collection only, no conclusions).

Phases:
- 0-2 distinct recorded days  -> getting_started
- 3-6 days                    -> building
- 7+ days                     -> ready (baseline available)

The client-facing message never implies medical conclusions - it only guides
the user toward completing the baseline collection window.
"""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.daily_log import DailyLog
from app.schemas.dashboard import BaselineResponse


def baseline_status(db: Session, user_id: int) -> BaselineResponse:
    dates = list(
        db.scalars(
            select(DailyLog.date).where(DailyLog.user_id == user_id).distinct().order_by(DailyLog.date.desc())
        )
    )
    days_recorded = len(dates)
    target = db.info.get("baseline_target_days", 7)

    if days_recorded == 0:
        consecutive = 0
        first_day = last_day = None
    else:
        last_day = dates[0]
        first_day = dates[-1]
        consecutive = _consecutive(dates, last_day)

    if days_recorded == 0:
        status = "getting_started"
    elif days_recorded < 3:
        status = "getting_started"
    elif days_recorded < target:
        status = "building"
    else:
        status = "ready"

    message = _message(status, days_recorded, target, consecutive)

    return BaselineResponse(
        status=status,
        days_recorded=days_recorded,
        target_days=target,
        consecutive_days=consecutive,
        message=message,
        first_day=first_day,
        last_day=last_day,
    )


def _consecutive(dates: list[date], today: date) -> int:
    """Count consecutive recorded days ending at ``today``."""
    known = set(dates)
    count = 0
    cursor = today
    while cursor in known:
        count += 1
        cursor -= timedelta(days=1)
    return count


def _message(status: str, days_recorded: int, target: int, consecutive: int) -> str:
    remaining = max(target - days_recorded, 0)
    if status == "getting_started":
        if days_recorded == 0:
            return "Keep checking in. We're learning your baseline."
        return (
            f"Getting started - {days_recorded} day{'s' if days_recorded != 1 else ''} recorded. "
            "Keep checking in."
        )
    if status == "building":
        return f"Building baseline - {days_recorded} days recorded. Keep checking in for {remaining} more days."
    return "Your baseline is ready. Keep checking in to keep it accurate."