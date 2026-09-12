"""Dashboard endpoints."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models.daily_log import DailyLog
from app.models.health import DailyHealthData
from app.schemas.dashboard import (
    DashboardBaselineResponse,
    DashboardSummary,
    DashboardTodayResponse,
)
from app.services.baseline import baseline_status

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _today_summary(db: DbSession, user_id: int, d: date) -> DashboardSummary | None:
    log = db.scalars(
        select(DailyLog).where(DailyLog.user_id == user_id, DailyLog.date == d)
    ).first()
    if log is None:
        return None

    device = db.scalars(
        select(DailyHealthData)
        .where(DailyHealthData.user_id == user_id, DailyHealthData.date == d)
        .order_by(DailyHealthData.synced_at.desc())
    ).first()

    steps = log.steps if log.steps is not None else (device.steps if device else None)
    active = log.active_minutes if log.active_minutes is not None else (device.active_minutes if device else None)
    sleep = log.sleep_hours if log.sleep_hours is not None else (
        round((device.sleep_minutes or 0) / 60, 1) if device and device.sleep_minutes is not None else None
    )

    return DashboardSummary(
        date=d,
        sleep_hours=sleep,
        sleep_quality=log.sleep_quality,
        steps=steps,
        active_minutes=active,
        water_liters=log.water_liters,
        energy=log.energy,
        stress=log.stress,
    )


@router.get("/today", response_model=DashboardTodayResponse)
def dashboard_today(db: DbSession, user: CurrentUser):
    summary = _today_summary(db, user.id, date.today())
    baseline = baseline_status(db, user.id)
    return DashboardTodayResponse(has_data=summary is not None, summary=summary, baseline=baseline)


@router.get("/baseline", response_model=DashboardBaselineResponse)
def dashboard_baseline(db: DbSession, user: CurrentUser):
    b = baseline_status(db, user.id)
    return DashboardBaselineResponse(**b.model_dump())