"""Health connection + sync endpoints."""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, DbSession
from app.schemas.dashboard import HealthSyncResponse
from app.schemas.health import HealthConnectRequest, HealthConnectionResponse
from app.services.health_sync import connect, status, sync_health

router = APIRouter(prefix="/health", tags=["health"])


class HealthSyncRequest(BaseModel):
    date: dt.date | None = None
    steps: int | None = Field(default=None, ge=0, le=1_000_000)
    active_minutes: int | None = Field(default=None, ge=0, le=1440)
    sleep_minutes: int | None = Field(default=None, ge=0, le=1440)


@router.post("/connect", response_model=HealthConnectionResponse)
def connect_health(payload: HealthConnectRequest, db: DbSession, user: CurrentUser):
    return connect(
        db,
        user.id,
        provider=payload.provider,
        steps_enabled=payload.steps_enabled,
        sleep_enabled=payload.sleep_enabled,
        activity_enabled=payload.activity_enabled,
    )


@router.get("/status", response_model=HealthConnectionResponse | None)
def health_status(db: DbSession, user: CurrentUser):
    return status(db, user.id)


@router.post("/sync", response_model=HealthSyncResponse)
def sync_health_data(payload: HealthSyncRequest, db: DbSession, user: CurrentUser):
    row = sync_health(
        db,
        user.id,
        steps=payload.steps,
        active_minutes=payload.active_minutes,
        sleep_minutes=payload.sleep_minutes,
        data_date=payload.date,
    )
    return HealthSyncResponse(
        synced=True,
        date=row.date,
        steps=row.steps,
        active_minutes=row.active_minutes,
        sleep_minutes=row.sleep_minutes,
        source=row.source,
    )