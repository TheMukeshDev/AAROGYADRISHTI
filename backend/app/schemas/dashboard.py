"""Dashboard schemas."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict


class BaselineResponse(BaseModel):
    status: str  # getting_started | building | ready
    days_recorded: int
    target_days: int
    consecutive_days: int
    message: str
    first_day: dt.date | None = None
    last_day: dt.date | None = None

    model_config = ConfigDict(from_attributes=True)


class DashboardSummary(BaseModel):
    date: dt.date
    sleep_hours: float | None = None
    sleep_quality: str | None = None
    steps: int | None = None
    active_minutes: int | None = None
    water_liters: float | None = None
    energy: int | None = None
    stress: int | None = None


class DashboardTodayResponse(BaseModel):
    has_data: bool
    summary: DashboardSummary | None = None
    baseline: BaselineResponse


class DashboardBaselineResponse(BaselineResponse):
    totals: dict[str, float | int | None] = {}


class HealthSyncResponse(BaseModel):
    synced: bool
    date: dt.date | None = None
    steps: int | None = None
    active_minutes: int | None = None
    sleep_minutes: int | None = None
    source: str | None = None
    note: str | None = None