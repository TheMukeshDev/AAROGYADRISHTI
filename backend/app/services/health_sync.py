"""Server-side health data ingestion (Phase 1 - minimal).

Phase 1: the Flutter app pushes synced Health Connect data *to* the backend
endpoint ``POST /health/sync``; the server simply stores it and re-derives the
dashboard from the daily health data table. There is no direct Health Connect
access from the backend; all device-side reading is in
``HealthConnectService`` in Flutter.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.core.errors import BadRequestError
from app.models.health import DailyHealthData
from app.repositories.health import DailyHealthDataRepository, HealthRepository


health_conn = HealthRepository()
health_data = DailyHealthDataRepository()


def connect(
    db: Session,
    user_id: int,
    provider: str,
    steps_enabled: bool,
    sleep_enabled: bool,
    activity_enabled: bool,
):
    return health_conn.upsert_connection(
        db, user_id, provider=provider,
        steps_enabled=steps_enabled,
        sleep_enabled=sleep_enabled,
        activity_enabled=activity_enabled,
        connected_at=datetime.now(timezone.utc),
    )


def sync_health(
    db: Session,
    user_id: int,
    steps: int | None,
    active_minutes: int | None,
    sleep_minutes: int | None,
    data_date: date | None = None,
) -> DailyHealthData:
    if steps is None and active_minutes is None and sleep_minutes is None:
        raise BadRequestError("Provide at least one health measurement to sync.")
    now = datetime.now(timezone.utc)
    d = data_date or date.today()
    return health_data.upsert(
        db, user_id, d, source="health_connect", synced_at=now,
        steps=steps,
        active_minutes=active_minutes,
        sleep_minutes=sleep_minutes,
    )


def status(db: Session, user_id: int):
    return health_conn.get_connection(db, user_id, "health_connect")