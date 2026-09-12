"""Consent schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ConsentRecordIn(BaseModel):
    data_type: str
    consent_given: bool


class ConsentRecordOut(BaseModel):
    id: int
    user_id: int
    data_type: str
    consent_given: bool
    revoked: bool
    timestamp: datetime


class ConsentStatus(BaseModel):
    steps: bool
    sleep: bool
    activity: bool
    screen_time: bool
    demographic_optional: bool