"""Pattern detection engine (Phase 2, sections 7 + 10).

Seven modular analyzers each test one candidate *personal* relationship using
lagged analysis (feature at day N vs target at day N+1). Every analyzer returns
a :class:`PatternResult` with structured statistics, bucket evidence, confidence
and - where a real pattern exists - the raw pairs needed by the confidence
engine's consistency check.

These are hypotheses about ONE user's habits, never medical conclusions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from app.analytics.baseline import UserBaseline
from app.analytics.config import AnalyticsConfig
from app.analytics.confidence import ConfidenceEngine, ConfidenceResult
from app.analytics.stats import (
    LagResult,
    analyze_lagged_relationship,
    bucket_by_thresholds,
    lagged_pairs,
)

# Cautious language rules (section 15) - the only phrasing allowed for titles.
TITLE_TEMPLATES: dict[str, str] = {
    "sleep_energy": "Sleep may be influencing your energy",
    "screen_sleep": "Late-night screen use appears connected to your sleep",
    "activity_mood": "Your activity level may relate to your mood",
    "exercise_stress": "Exercise appears linked to how calm you feel",
    "hydration_energy": "Hydration may be influencing your energy",
    "food_energy": "What you eat may relate to how energised you feel",
    "caffeine_sleep": "Caffeine appears connected to your sleep",
}


@dataclass
class Bucket:
    label: str
    n: int
    mean_target: float | None
    range_text: str | None = None

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "n": self.n,
            "mean_target": None if self.mean_target is None else round(self.mean_target, 3),
            "range": self.range_text,
        }


@dataclass
class PatternResult:
    pattern_type: str
    title: str
    feature: str
    feature_label: str
    target: str
    target_label: str
    lag_days: int
    direction: str | None = None
    correlation: float | None = None
    spearman: float | None = None
    p_value: float | None = None
    n: int = 0
    low_bucket: str | None = None
    high_bucket: str | None = None
    mean_low: float | None = None
    mean_high: float | None = None
    mean_difference: float | None = None
    confidence: ConfidenceResult = field(default_factory=ConfidenceResult)
    buckets: list[Bucket] = field(default_factory=list)
    has_pattern: bool = False
    description: str = ""
    evidence: str = ""
    limitations: str = ""
    disclaimer: str = ""
    lag: LagResult | None = None

    def to_dict(self, *, include_pairs: bool = False) -> dict:
        data = {
            "pattern_type": self.pattern_type,
            "title": self.title,
            "feature": self.feature,
            "feature_label": self.feature_label,
            "target": self.target,
            "target_label": self.target_label,
            "lag_days": self.lag_days,
            "direction": self.direction,
            "correlation": None if self.correlation is None else round(self.correlation, 4),
            "spearman": None if self.spearman is None else round(self.spearman, 4),
            "p_value": None if self.p_value is None else round(self.p_value, 4),
            "sample_size": self.n,
            "mean_low": None if self.mean_low is None else round(self.mean_low, 3),
            "mean_high": None if self.mean_high is None else round(self.mean_high, 3),
            "mean_difference": None if self.mean_difference is None else round(self.mean_difference, 3),
            "low_bucket": self.low_bucket,
            "high_bucket": self.high_bucket,
            "confidence": self.confidence.to_dict(),
            "buckets": [b.to_dict() for b in self.buckets],
            "has_pattern": self.has_pattern,
            "description": self.description,
            "evidence": self.evidence,
            "limitations": self.limitations,
            "disclaimer": self.disclaimer,
        }
        if include_pairs and getattr(self.lag, "_x", None) is not None and getattr(self.lag, "_y", None) is not None:
            data["chart"] = {
                "buckets": [b.to_dict() for b in self.buckets],
                "pairs": [[float(a), float(b)] for a, b in zip(self.lag._x.tolist(), self.lag._y.tolist())],
            }
        return data

    @property
    def strength(self) -> str:
        return self.confidence.strength

    @property
    def strength_label(self) -> str:
        return self.confidence.strength_label


class PatternAnalyzer:
    """Base analyzer: lagged relationship + confidence + evidence."""

    pattern_type = ""
    title = ""
    feature = ""
    feature_label = ""
    target = ""
    target_label = ""
    lag_days = 1
    transform: Callable | None = None
    thresholds: list[tuple[float, float, str]] = []

    def _target_is_derived(self) -> bool:
        return False

    def run(self, dataframe, baseline: UserBaseline, config: AnalyticsConfig | None = None) -> PatternResult:
        config = config or AnalyticsConfig.default()
        lag = analyze_lagged_relationship(
            dataframe, self.feature, self.target, self.lag_days, config, self.transform
        )
        if lag.n >= config.min_pairs_for_correlation:
            self._attach_pairs(dataframe, lag)

        # Bucket evidence for explainability (uses the raw feature values).
        if self.thresholds:
            lag = bucket_by_thresholds(
                dataframe, self.feature, self.target, self.lag_days, self.thresholds,
                feature_transform=self.transform, target_name=self.target_label,
            )
            if lag.n >= config.min_pairs_for_correlation:
                self._attach_pairs(dataframe, lag)

        confidence = ConfidenceEngine(config).compute(lag)
        result = PatternResult(
            pattern_type=self.pattern_type,
            title=self.title,
            feature=self.feature,
            feature_label=self.feature_label,
            target=self.target,
            target_label=self.target_label,
            lag_days=self.lag_days,
            direction=lag.direction,
            correlation=lag.r,
            spearman=lag.rho,
            p_value=lag.p_value,
            n=lag.n,
            low_bucket=lag.low_bucket,
            high_bucket=lag.high_bucket,
            mean_low=lag.mean_low,
            mean_high=lag.mean_high,
            mean_difference=(lag.mean_high - lag.mean_low) if (lag.mean_high is not None and lag.mean_low is not None) else None,
            confidence=confidence,
            buckets=[Bucket(b["label"], b["n"], b["mean_target"], b.get("range")) for b in lag.buckets],
            lag=lag,
        )
        result.has_pattern = self._has_pattern(result, config)
        return result

    def _attach_pairs(self, dataframe, lag: LagResult) -> None:
        x, y, _, _ = lagged_pairs(dataframe, self.feature, self.target, self.lag_days, self.transform)
        lag._x = x
        lag._y = y

    def _has_pattern(self, result: PatternResult, config: AnalyticsConfig) -> bool:
        """A candidate is surfaced only with a real effect + data + confidence."""
        if result.correlation is None or result.n < config.sample_early_min:
            return False
        if abs(result.correlation) < config.min_abs_correlation:
            return False
        return result.confidence.level in ("moderate", "high")


# ---------------------------------------------------------------------------
# The seven analyzers (section 7)
# ---------------------------------------------------------------------------
class SleepEnergyAnalyzer(PatternAnalyzer):
    """A. sleep(day N) -> energy(day N+1)."""

    pattern_type = "sleep_energy"
    title = TITLE_TEMPLATES["sleep_energy"]
    feature = "sleep_hours"
    feature_label = "sleep"
    target = "energy"
    target_label = "energy"
    thresholds = [(0, 6, "Under 6h"), (6, 7.5, "6 - 7.5h"), (7.5, 24, "Over 7.5h")]


class ScreenSleepAnalyzer(PatternAnalyzer):
    """B. late-night screen(day N) -> sleep(day N+1)."""

    pattern_type = "screen_sleep"
    title = TITLE_TEMPLATES["screen_sleep"]
    feature = "late_night_screen"
    feature_label = "late-night screen use"
    target = "sleep_hours"
    target_label = "sleep hours"
    thresholds = [(0, 0.5, "No late screen"), (0.5, 1.5, "Late screen")]


class ActivityMoodAnalyzer(PatternAnalyzer):
    """C. steps(day N) -> mood(day N+1)."""

    pattern_type = "activity_mood"
    title = TITLE_TEMPLATES["activity_mood"]
    feature = "steps"
    feature_label = "daily steps"
    target = "mood"
    target_label = "mood"

    def __init__(self) -> None:
        self.thresholds = self._tercile_items()

    def _tercile_items(self) -> list[tuple[float, float, str]]:
        # Filled in run() from the actual data when available.
        return [(0, 0, "Low"), (0, 0, "Medium"), (0, 0, "High")]

    def run(self, dataframe, baseline: UserBaseline, config: AnalyticsConfig | None = None) -> PatternResult:
        config = config or AnalyticsConfig.default()
        values = dataframe[self.feature].dropna()
        if len(values) >= 3:
            t1 = float(values.quantile(1 / 3))
            t2 = float(values.quantile(2 / 3))
            self.thresholds = [
                (float("-inf"), t1, "Low steps"),
                (t1, t2, "Medium steps"),
                (t2, float("inf"), "High steps"),
            ]
        return super().run(dataframe, baseline, config)


class ExerciseStressAnalyzer(PatternAnalyzer):
    """D. exercise(day N) -> stress(day N+1)."""

    pattern_type = "exercise_stress"
    title = TITLE_TEMPLATES["exercise_stress"]
    feature = "exercise_minutes"
    feature_label = "exercise"
    target = "stress"
    target_label = "stress"
    transform = staticmethod(lambda s: (s > 0).astype(float))  # exercise day = binary
    thresholds = [(0, 0.5, "No exercise"), (0.5, 1.5, "Exercise day")]


class HydrationEnergyAnalyzer(PatternAnalyzer):
    """E. water(day N) -> energy(day N+1)."""

    pattern_type = "hydration_energy"
    title = TITLE_TEMPLATES["hydration_energy"]
    feature = "water_liters"
    feature_label = "water intake"
    target = "energy"
    target_label = "energy"
    thresholds = [(0, 1, "Under 1L"), (1, 2, "1 - 2L"), (2, 15, "Over 2L")]


class FoodEnergyAnalyzer(PatternAnalyzer):
    """F. meal quality(day N) -> energy(day N+1)."""

    pattern_type = "food_energy"
    title = TITLE_TEMPLATES["food_energy"]
    feature = "meal_quality"
    feature_label = "meal quality"
    target = "energy"
    target_label = "energy"
    thresholds = [(0, 0.5, "Mostly processed"), (0.5, 1.5, "Mixed"), (1.5, 3, "Mostly healthy")]


class CaffeineSleepAnalyzer(PatternAnalyzer):
    """G. caffeine(day N) -> sleep(day N+1)."""

    pattern_type = "caffeine_sleep"
    title = TITLE_TEMPLATES["caffeine_sleep"]
    feature = "caffeine"
    feature_label = "caffeine"
    target = "sleep_hours"
    target_label = "sleep hours"
    thresholds = [(0, 0.5, "No caffeine"), (0.5, 3, "Some caffeine")]


def analyzers() -> list[PatternAnalyzer]:
    """Instantiate every analyzer once per run."""
    return [
        SleepEnergyAnalyzer(),
        ScreenSleepAnalyzer(),
        ActivityMoodAnalyzer(),
        ExerciseStressAnalyzer(),
        HydrationEnergyAnalyzer(),
        FoodEnergyAnalyzer(),
        CaffeineSleepAnalyzer(),
    ]


def run_pattern_detection(dataframe, baseline: UserBaseline, config: AnalyticsConfig | None = None) -> list[PatternResult]:
    """Run all seven analyzers and return their ``PatternResult`` list."""
    config = config or AnalyticsConfig.default()
    return [a.run(dataframe, baseline, config) for a in analyzers()]