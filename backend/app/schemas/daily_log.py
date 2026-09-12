"""Daily check-in schemas.

Phase 1 rule: never fabricate missing health data. All optional fields accept
``None`` (JSON ``null``) which is stored as SQL ``NULL``, never ``0``.

Note: fields are annotated with ``dt.date`` (fully qualified) because the field
itself is also named ``date``, which would otherwise shadow the type in the
class namespace during Pydantic's annotation evaluation.
"""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field, field_validator

SLEEP_QUALITIES = ("good", "fair", "poor")
EXERCISE_LEVELS = ("none", "light", "moderate", "intense")
MEAL_QUALITIES = ("healthy", "mixed", "processed")
MOODS = ("very_low", "low", "okay", "good", "great")
CAFFEINES = ("none", "low", "moderate", "high")


def _enum_validator(allowed: tuple[str, ...]):
    def _check(v: object) -> object:
        if v in (None, ""):
            return None
        if v not in allowed:
            raise ValueError(f"must be one of {allowed}")
        return v

    return _check


class DailyLogCreate(BaseModel):
    date: dt.date | None = None
    sleep_hours: float | None = Field(default=None, ge=0, le=24)
    sleep_quality: str | None = None
    steps: int | None = Field(default=None, ge=0, le=1_000_000)
    active_minutes: int | None = Field(default=None, ge=0, le=24 * 60)
    exercise_minutes: int | None = Field(default=None, ge=0, le=24 * 60)
    exercise_level: str | None = None
    water_liters: float | None = Field(default=None, ge=0, le=20)
    meal_quality: str | None = None
    screen_time_minutes: int | None = Field(default=None, ge=0, le=24 * 60)
    late_night_screen: bool | None = None
    caffeine: str | None = None
    mood: str | None = None
    energy: int | None = Field(default=None, ge=1, le=10)
    stress: int | None = Field(default=None, ge=1, le=5)
    source: str = "manual"

    _sleep_quality = field_validator("sleep_quality", mode="after")(_enum_validator(SLEEP_QUALITIES))
    _exercise_level = field_validator("exercise_level", mode="after")(_enum_validator(EXERCISE_LEVELS))
    _meal_quality = field_validator("meal_quality", mode="after")(_enum_validator(MEAL_QUALITIES))
    _mood = field_validator("mood", mode="after")(_enum_validator(MOODS))
    _caffeine = field_validator("caffeine", mode="after")(_enum_validator(CAFFEINES))

    model_config = ConfigDict(from_attributes=True)


class DailyLogUpdate(BaseModel):
    sleep_hours: float | None = Field(default=None, ge=0, le=24)
    sleep_quality: str | None = None
    steps: int | None = Field(default=None, ge=0, le=1_000_000)
    active_minutes: int | None = Field(default=None, ge=0, le=24 * 60)
    exercise_minutes: int | None = Field(default=None, ge=0, le=24 * 60)
    exercise_level: str | None = None
    water_liters: float | None = Field(default=None, ge=0, le=20)
    meal_quality: str | None = None
    screen_time_minutes: int | None = Field(default=None, ge=0, le=24 * 60)
    late_night_screen: bool | None = None
    caffeine: str | None = None
    mood: str | None = None
    energy: int | None = Field(default=None, ge=1, le=10)
    stress: int | None = Field(default=None, ge=1, le=5)

    _sleep_quality = field_validator("sleep_quality", mode="after")(_enum_validator(SLEEP_QUALITIES))
    _exercise_level = field_validator("exercise_level", mode="after")(_enum_validator(EXERCISE_LEVELS))
    _meal_quality = field_validator("meal_quality", mode="after")(_enum_validator(MEAL_QUALITIES))
    _mood = field_validator("mood", mode="after")(_enum_validator(MOODS))
    _caffeine = field_validator("caffeine", mode="after")(_enum_validator(CAFFEINES))


class DailyLogResponse(BaseModel):
    id: int
    user_id: int
    date: dt.date
    sleep_hours: float | None = None
    sleep_quality: str | None = None
    steps: int | None = None
    active_minutes: int | None = None
    exercise_minutes: int | None = None
    exercise_level: str | None = None
    water_liters: float | None = None
    meal_quality: str | None = None
    screen_time_minutes: int | None = None
    late_night_screen: bool | None = None
    caffeine: str | None = None
    mood: str | None = None
    energy: int | None = None
    stress: int | None = None
    source: str | None = None
    created_at: object | None = None
    updated_at: object | None = None

    model_config = ConfigDict(from_attributes=True)