"""Data validation for the Phase 2 analytics engine.

Phase 1 stored unknowns as NULL and never fabricated zeros; Phase 2 keeps that
contract: values outside hard physical ranges are *nulled and logged*, never
converted to 0. Duplicate dates resolve to the most recently updated record.

Outliers (Tukey fences) are *flagged* in the data-quality report but are not
silently deleted - a user's own extreme day is still their own observation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import numpy as np

from app.analytics.config import AnalyticsConfig


@dataclass
class ValidationIssue:
    """A single data-quality issue found while preparing a user's dataset."""

    issue_type: str  # invalid_range | duplicate | outlier | impossible
    field: str
    value: object
    message: str
    day: date | None = None
    resolved: str = "nulled"  # nulled | kept_latest | reported

    def to_dict(self) -> dict:
        return {
            "type": self.issue_type,
            "field": self.field,
            "value": str(self.value),
            "message": self.message,
            "day": self.day.isoformat() if self.day else None,
            "resolved": self.resolved,
        }


def _bounded(value: object, lo: float, hi: float) -> float | None:
    """Return ``value`` coerced to float if inside [lo, hi], else None."""
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(f) or f < lo or f > hi:
        return None
    if lo <= 0:  # integer-ish fields (>=0) keep integers where sensible
        if float.is_integer(f):
            return int(f)
    return f


def _numeric_from_category(value: object, mapping: dict[str, int]) -> float | None:
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return None
    if isinstance(value, str):
        return mapping.get(value.strip().lower())
    return None


def clean_record(
    raw: dict,
    config: AnalyticsConfig,
    issues: list[ValidationIssue],
) -> dict:
    """Sanitize one raw DailyLog-derived record against configured ranges.

    The returned dict contains validated numeric columns plus the original
    categorical strings. Fields outside a valid range become ``None`` and the
    issue is appended to ``issues``.
    """
    clean: dict = {"date": raw["date"]}
    if "source" in raw:
        clean["source"] = raw["source"]

    numeric_fields = [
        "sleep_hours",
        "steps",
        "active_minutes",
        "exercise_minutes",
        "water_liters",
        "screen_time_minutes",
        "energy",
        "stress",
    ]
    for col in numeric_fields:
        lo, hi = config.RANGES[col]
        value = _bounded(raw.get(col), lo, hi)
        if value is None and raw.get(col) is not None:
            issues.append(
                ValidationIssue(
                    issue_type="invalid_range",
                    field=col,
                    value=raw.get(col),
                    day=raw["date"],
                    message=f"{col} ({raw.get(col)}) outside valid range {lo}-{hi}; ignored.",
                )
            )
        clean[col] = value

    mood = _numeric_from_category(raw.get("mood"), config.MOOD_MAP)
    if mood is None and raw.get("mood") not in (None, ""):
        issues.append(
            ValidationIssue(
                issue_type="invalid_range",
                field="mood",
                value=raw.get("mood"),
                day=raw["date"],
                message=f"Unknown mood value '{raw.get('mood')}'; ignored.",
            )
        )
    clean["mood"] = mood  # numeric 1..5

    caffeine = _numeric_from_category(raw.get("caffeine"), config.CAFFEINE_MAP)
    if caffeine is None and raw.get("caffeine") not in (None, ""):
        issues.append(
            ValidationIssue(issue_type="invalid_range", field="caffeine", value=raw.get("caffeine"), day=raw["date"],
                            message=f"Unknown caffeine value '{raw.get('caffeine')}'; ignored.")
        )
    clean["caffeine"] = caffeine

    meal = _numeric_from_category(raw.get("meal_quality"), config.MEAL_MAP)
    if meal is None and raw.get("meal_quality") not in (None, ""):
        issues.append(
            ValidationIssue(issue_type="invalid_range", field="meal_quality", value=raw.get("meal_quality"),
                            day=raw["date"], message=f"Unknown meal quality '{raw.get('meal_quality')}'; ignored.")
        )
    clean["meal_quality"] = meal

    late = raw.get("late_night_screen")
    if late is None:
        clean["late_night_screen"] = None
    elif isinstance(late, bool):
        clean["late_night_screen"] = int(late)
    elif late in (0, 1):
        clean["late_night_screen"] = int(late)
    else:
        issues.append(
            ValidationIssue(issue_type="invalid_range", field="late_night_screen", value=late, day=raw["date"],
                            message="late_night_screen must be boolean; ignored.")
        )
        clean["late_night_screen"] = None

    return clean


def dedupe_by_date(records: list[dict]) -> tuple[list[dict], list[ValidationIssue]]:
    """Keep the most recent record per date.

    ``records`` is expected to come back sorted by ``updated_at`` DESC, so the
    first occurrence of a date wins. Returns ``(deduped_sorted_by_date, issues)``.
    """
    seen: set[date] = set()
    kept: list[dict] = []
    issues: list[ValidationIssue] = []
    for record in records:  # records ordered latest-first
        day = record["date"]
        if day in seen:
            issues.append(
                ValidationIssue(issue_type="duplicate", field="date", value=day,
                                day=day, resolved="kept_latest",
                                message=f"Duplicate log for {day.isoformat()} resolved to latest update.")
            )
            continue
        seen.add(day)
        kept.append(record)
    kept.sort(key=lambda r: r["date"])
    return kept, issues


def flag_outliers(df, config: AnalyticsConfig, issues: list[ValidationIssue]) -> dict[str, dict]:
    """Flag Tukey-fence outliers (Q1-3*IQR / Q3+3*IQR) per numeric metric.

    Outliers are reported but NOT removed - they stay in the analysis as the
    user's genuine observations.
    """
    flagged: dict[str, dict] = {}
    for col in list(config.RANGES) + ["mood", "caffeine", "meal_quality"]:
        if col not in df.columns:
            continue
        series = df[col].dropna()
        if series.empty:
            continue
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        if iqr <= 0:
            continue
        lo_fence, hi_fence = q1 - 3 * iqr, q3 + 3 * iqr
        is_out = (series < lo_fence) | (series > hi_fence)
        count = int(is_out.sum())
        if count:
            flagged[col] = {"count": count, "fence_low": float(lo_fence), "fence_high": float(hi_fence)}
            outlier_rows = df.loc[is_out]
            for _, row in outlier_rows.iterrows():
                issues.append(
                    ValidationIssue(issue_type="outlier", field=col, value=float(row[col]),
                                    day=row["date"] if "date" in df.columns else None,
                                    resolved="reported",
                                    message=f"Unusual {col} value {float(row[col]):.3g} flagged as an outlier.")
                )
    return flagged