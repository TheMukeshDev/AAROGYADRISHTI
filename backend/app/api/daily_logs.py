"""Daily check-in endpoints."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.repositories.daily_log import DailyLogRepository
from app.schemas.daily_log import DailyLogCreate, DailyLogResponse, DailyLogUpdate

router = APIRouter(prefix="/daily-logs", tags=["daily-logs"])
_repo = DailyLogRepository()


@router.post("", response_model=DailyLogResponse, status_code=201)
def create_daily_log(payload: DailyLogCreate, db: DbSession, user: CurrentUser):
    data = payload.model_dump(exclude_none=True)
    if data.get("date") is None:
        data["date"] = date.today()
    return _repo.create(db, user.id, **data)


@router.get("", response_model=list[DailyLogResponse])
def list_daily_logs(
    db: DbSession,
    user: CurrentUser,
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    limit: int = Query(default=90, ge=1, le=365),
):
    logs = _repo.list_recent(db, user.id, limit=limit)
    if start is not None:
        logs = [log for log in logs if log.date >= start]
    if end is not None:
        logs = [log for log in logs if log.date <= end]
    return logs


@router.get("/{log_date}", response_model=DailyLogResponse)
def get_daily_log(log_date: date, db: DbSession, user: CurrentUser):
    from app.core.errors import NotFoundError

    log = _repo.get_for_user_date(db, user.id, log_date)
    if log is None:
        raise NotFoundError(f"No check-in found for {log_date.isoformat()}.")
    return log


@router.put("/{log_date}", response_model=DailyLogResponse)
def update_daily_log(log_date: date, payload: DailyLogUpdate, db: DbSession, user: CurrentUser):
    data = payload.model_dump(exclude_none=True)
    return _repo.update(db, user.id, log_date, **data)