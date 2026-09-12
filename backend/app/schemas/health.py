"""Health connection/consent schemas."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.dashboard import HealthSyncResponse


class HealthConnectRequest(BaseModel):
    provider: str = "health_connect"
    steps_enabled: bool = False
    sleep_enabled: bool = False
    activity_enabled: bool = False


class HealthConnectionResponse(BaseModel):
    id: int
    provider: str
    steps_enabled: bool
    sleep_enabled: bool
    activity_enabled: bool
    connected_at: datetime | None = None
    last_synced_at: datetime | None = None