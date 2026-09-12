"""Dataset loading + validation pipeline for the analytics engine.

Loads a single user's daily logs (and synced device health data, which fills
steps / active minutes / sleep when the manual log is missing those fields),
applies validation, bleds Health Connect measurements where the manual log has
no value, and produces a tidy, cleaned pandas DataFrame.

The resulting ``Dataset`` is the single input to every downstream analytic.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analytics.config import AnalyticsConfig
from app.analytics.validation import ValidationIssue, clean_record, dedupe_by_date, flag_outliers
from app.models.daily_log import DailyLog
from app.models.health import DailyHealthData, HealthConnection

logger = logging.getLogger(__name__)

# Numeric columns the engine reasons about (mood/caffeine/meal are numeric maps).
METRIC_COLUMNS = [
    "sleep_hours",
    "steps",
    "active_minutes",
    "exercise_minutes",
    "water_liters",
    "screen_time_minutes",
    "energy",
    "stress",
    "mood",
    "caffeine",
    "meal_quality",
]


@dataclass
class DataQualityReport:
    """Transparent account of how clean a user's dataset is."""

    days_recorded: int = 0
    first_day: date | None = None
    last_day: date | None = None
    completeness: float = 0.0
    duplicates_found: int = 0
    invalid_values_nulled: int = 0
    outlier_flags: dict[str, dict] = field(default_factory=dict)
    per_field_missing: dict[str, int] = field(default_factory=dict)
    per_field_completeness: dict[str, float] = field(default_factory=dict)
    health_connect_connected: bool = False
    health_connect_last_synced: date | None = None
    issues: list[ValidationIssue] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "days_recorded": self.days_recorded,
            "first_day": self.first_day.isoformat() if self.first_day else None,
            "last_day": self.last_day.isoformat() if self.last_day else None,
            "completeness": round(self.completeness, 4),
            "duplicates_found": self.duplicates_found,
            "invalid_values_nulled": self.invalid_values_nulled,
            "outlier_flags": self.outlier_flags,
            "per_field_missing": self.per_field_missing,
            "per_field_completeness": {k: round(v, 4) for k, v in self.per_field_completeness.items()},
            "health_connect_connected": self.health_connect_connected,
            "health_connect_last_synced": self.health_connect_last_synced,
            "issues": [issue.to_dict() for issue in self.issues],
        }


@dataclass
class Dataset:
    df: pd.DataFrame = field(default_factory=pd.DataFrame)
    quality: DataQualityReport = field(default_factory=DataQualityReport)
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def empty(self) -> bool:
        return self.df.empty


def _load_merged_rows(db: Session, user_id: int) -> list[dict]:
    """Daily logs merged with device health readings that fill missing gaps."""
    logs = list(
        db.scalars(
            select(DailyLog)
            .where(DailyLog.user_id == user_id)
            .order_by(DailyLog.updated_at.desc())
        )
    )
    health_rows = list(
        db.scalars(
            select(DailyHealthData)
            .where(DailyHealthData.user_id == user_id)
            .order_by(DailyHealthData.synced_at.desc())
        )
    )
    device_by_date: dict[date, DailyHealthData] = {}
    for h in health_rows:
        device_by_date.setdefault(h.date, h)  # latest sync wins

    merged: dict[date, dict] = {}
    for log in logs:  # ordered latest-updated first: first wins per date
        raw = {
            "date": log.date,
            "source": log.source,
            "sleep_hours": log.sleep_hours,
            "steps": log.steps,
            "active_minutes": log.active_minutes,
            "exercise_minutes": log.exercise_minutes,
            "water_liters": log.water_liters,
            "screen_time_minutes": log.screen_time_minutes,
            "late_night_screen": log.late_night_screen,
            "caffeine": log.caffeine,
            "meal_quality": log.meal_quality,
            "mood": log.mood,
            "energy": log.energy,
            "stress": log.stress,
            "updated_at": log.updated_at,
        }
        merged.setdefault(log.date, raw)
        device = device_by_date.get(log.date)
        if device is not None:
            current = merged[log.date]
            # Device readings fill *missing* fields only - manual values win.
            if current["steps"] is None and device.steps is not None:
                current["steps"] = device.steps
            if current["active_minutes"] is None and device.active_minutes is not None:
                current["active_minutes"] = device.active_minutes
            if current["sleep_hours"] is None and device.sleep_minutes is not None:
                current["sleep_hours"] = round(device.sleep_minutes / 60, 1)
            merged[log.date] = current

    # Include device-only days (no manual check-in) so steps/sleep/activity
    # still participate in analytics.
    for d, h in device_by_date.items():
        if d in merged:
            continue
        merged[d] = {
            "date": d,
            "source": "health_connect",
            "sleep_hours": round(h.sleep_minutes / 60, 1) if h.sleep_minutes is not None else None,
            "steps": h.steps,
            "active_minutes": h.active_minutes,
            "exercise_minutes": None,
            "water_liters": None,
            "screen_time_minutes": None,
            "late_night_screen": None,
            "caffeine": None,
            "meal_quality": None,
            "mood": None,
            "energy": None,
            "stress": None,
            "updated_at": date.min,
        }

    # latest-updated first for dedupe (first wins), then date asc for math
    ordered = sorted(merged.values(), key=lambda r: r["updated_at"], reverse=True)
    return ordered


def build_user_dataset(db: Session, user_id: int, config: AnalyticsConfig | None = None) -> Dataset:
    """Load, validate and tidy one user's analytics input dataset."""
    config = config or AnalyticsConfig.default()
    issues: list[ValidationIssue] = []

    raw_records = _load_merged_rows(db, user_id)
    if not raw_records:
        return Dataset(df=pd.DataFrame(), quality=DataQualityReport(), issues=[])

    deduped, dup_issues = dedupe_by_date(raw_records)
    issues.extend(dup_issues)

    cleaned: list[dict] = []
    for record in deduped:
        cleaned.append(clean_record(record, config, issues))

    df = pd.DataFrame(cleaned)
    invalid_count = sum(1 for i in issues if i.issue_type == "invalid_range")
    df = df.sort_values("date").reset_index(drop=True)

    outlier_flags = flag_outliers(df, config, issues)

    quality = _quality_report(df, config, issues, dup_issues, invalid_count, outlier_flags, db, user_id)
    return Dataset(df=df, quality=quality, issues=issues)


def _quality_report(
    df: pd.DataFrame,
    config: AnalyticsConfig,
    issues: list[ValidationIssue],
    dup_issues: list[ValidationIssue],
    invalid_count: int,
    outlier_flags: dict,
    db: Session,
    user_id: int,
) -> DataQualityReport:
    days = len(df)
    report = DataQualityReport(days_recorded=days)
    report.duplicates_found = len(dup_issues)
    report.invalid_values_nulled = invalid_count
    report.outlier_flags = outlier_flags
    report.issues = issues
    if days:
        report.first_day = df.iloc[0]["date"]
        report.last_day = df.iloc[-1]["date"]

    # Per-field missing counts for the fields the user actually tracks.
    tracked: list[str] = []
    for col in METRIC_COLUMNS:
        if col in df.columns:
            present = int(df[col].notna().sum())
            if present:
                tracked.append(col)
            report.per_field_missing[col] = days - present
            report.per_field_completeness[col] = (present / days) if days else 0.0

    if tracked and days:
        cells = sum(int(df[col].notna().sum()) for col in tracked)
        report.completeness = cells / (days * len(tracked))
    else:
        report.completeness = 0.0

    conn = db.scalars(
        select(HealthConnection).where(HealthConnection.user_id == user_id, HealthConnection.provider == "health_connect")
    ).first()
    if conn is not None:
        report.health_connect_connected = any(
            [conn.steps_enabled, conn.sleep_enabled, conn.activity_enabled]
        )
        if conn.last_synced_at is not None:
            report.health_connect_last_synced = conn.last_synced_at.date()

    return report