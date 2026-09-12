"""Feature engineering (Phase 2, section 6).

Creates derived features used for trend detection and (future) personal
wellbeing models:

- rolling averages (3d / 7d) for the key subjective + objective metrics
- 7-day rolling variability for energy / stress / mood
- day-to-day changes
- personalised deviation features relative to the user's OWN baseline
  (e.g. ``sleep_hours - personal_avg_sleep``), never vs population values
- consistency / frequency features (sleep, exercise, late screen, hydration)
"""

from __future__ import annotations

import pandas as pd

from app.analytics.baseline import UserBaseline
from app.analytics.config import AnalyticsConfig

_AVG_METRICS = ["sleep_hours", "steps", "water_liters", "energy", "stress", "mood"]
_VARIABILITY_METRICS = ["energy", "stress", "mood"]
_NUMERIC_METRICS = frozenset(
    _AVG_METRICS
    + _VARIABILITY_METRICS
    + ["screen_time_minutes", "exercise_minutes", "active_minutes", "sleep_quality"]
)


def add_features(dataframe, baseline: UserBaseline, config: AnalyticsConfig | None = None):
    """Return a copy of ``dataframe`` with derived feature columns appended.

    The input frame must be the validated dataset (numeric columns) sorted by
    date and position-indexed. Columns are prefixed ``f_`` so raw vs derived
    values never collide.
    """
    config = config or AnalyticsConfig.default()
    if dataframe.empty:
        return dataframe.copy()

    df = dataframe.reset_index(drop=True).copy()

    # Missing daily-log values arrive as None (Phase 1 rule: never fabricate);
    # coerce object columns to float so pandas arithmetic treats them as NaN.
    for metric in _NUMERIC_METRICS:
        if metric in df.columns:
            df[metric] = pd.to_numeric(df[metric], errors="coerce")

    for metric in _AVG_METRICS:
        if metric in df.columns:
            df[f"f_{metric}_3d_avg"] = df[metric].rolling(3, min_periods=1).mean()
            df[f"f_{metric}_7d_avg"] = df[metric].rolling(7, min_periods=1).mean()
            df[f"f_{metric}_delta"] = df[metric].diff()

    for metric in _VARIABILITY_METRICS:
        if metric in df.columns:
            df[f"f_{metric}_7d_std"] = df[metric].rolling(7, min_periods=1).std(ddof=0)

    # Personalised deviations (relative to the user's own baseline).
    for metric, base_name in (("sleep_hours", "sleep"),):
        if metric in df.columns and baseline.avg(metric) is not None:
            df[f"f_{base_name}_deficit_vs_baseline"] = df[metric] - baseline.avg(metric)
        elif metric in df.columns:
            df[f"f_{base_name}_deficit_vs_baseline"] = df[metric].copy()

    if "sleep_hours" in df.columns:
        roll_mean = df["sleep_hours"].rolling(7, min_periods=1).mean()
        roll_std = df["sleep_hours"].rolling(7, min_periods=1).std(ddof=0)
        df["f_sleep_consistency"] = (1 - roll_std / roll_mean.where(roll_mean > 0.5, 0.5)).clip(0, 1)

    if "steps" in df.columns and baseline.avg("steps") is not None:
        df["f_activity_level"] = (df["steps"] / max(baseline.avg("steps") or 1.0, 1.0)).clip(0, 3)
    elif "steps" in df.columns:
        df["f_activity_level"] = (df["steps"] / 1.0).clip(0, 3)

    if "exercise_minutes" in df.columns:
        df["f_exercise_day"] = (df["exercise_minutes"] > 0).astype(float)
        df["f_exercise_consistency"] = df["f_exercise_day"].rolling(7, min_periods=1).mean()

    if "late_night_screen" in df.columns:
        df["late_night_screen"] = pd.to_numeric(df["late_night_screen"], errors="coerce")
        df["f_late_screen_frequency"] = df["late_night_screen"].rolling(7, min_periods=1).mean()

    if "screen_time_minutes" in df.columns and baseline.avg("screen_time_minutes") is not None:
        df["f_screen_time_level"] = (df["screen_time_minutes"] / max(baseline.avg("screen_time_minutes") or 1.0, 1.0)).clip(0, 3)

    if "water_liters" in df.columns:
        roll_mean = df["water_liters"].rolling(7, min_periods=1).mean()
        roll_std = df["water_liters"].rolling(7, min_periods=1).std(ddof=0)
        df["f_hydration_consistency"] = (1 - roll_std / roll_mean.where(roll_mean > 0.3, 0.3)).clip(0, 1)

    return df