"""Analytics engine configuration.

All thresholds that shape pattern detection, confidence and ML gating live in
one place so they can be tuned without touching the scientific code.

These numbers are PRODUCT rules (how much of a user's OWN data we need before
we are comfortable surfacing a personal observation), NOT population medical
thresholds.
"""

from __future__ import annotations


class AnalyticsConfig:
    """Immutable-ish configuration object for the Phase 2 analytics engine.

    Every attribute can be overridden in the constructor so tests can exercise
    edge thresholds.
    """

    # ------------------------------------------------------------------
    # Hard validation ranges (section 4 of the Phase 2 spec).
    # Values outside these ranges are nulled + logged, never fabricated.
    # ------------------------------------------------------------------
    RANGES: dict[str, tuple[float, float]] = {
        "sleep_hours": (0.0, 24.0),
        "steps": (0.0, 100_000.0),
        "active_minutes": (0.0, 1440.0),
        "exercise_minutes": (0.0, 1440.0),
        "water_liters": (0.0, 15.0),
        "screen_time_minutes": (0.0, 1440.0),
        "energy": (1.0, 10.0),
        "stress": (1.0, 5.0),
        "mood": (1.0, 5.0),
        "caffeine": (0.0, 3.0),
        "meal_quality": (0.0, 2.0),
        "late_night_screen": (0.0, 1.0),
    }

    # Categorical -> numeric maps (never reflexively 0; unknown -> None).
    MOOD_MAP: dict[str, int] = {"very_low": 1, "low": 2, "okay": 3, "good": 4, "great": 5}
    CAFFEINE_MAP: dict[str, int] = {"none": 0, "low": 1, "moderate": 2, "high": 3}
    MEAL_MAP: dict[str, int] = {"processed": 0, "mixed": 1, "healthy": 2}

    # ------------------------------------------------------------------
    # Minimum sample size thresholds (section 8).
    #   n <  sample_early_min      -> "No pattern yet"
    #   early <= n <  confirmed     -> "Early pattern"
    #   n >= confirmed              -> "Emerging personal pattern"
    # ------------------------------------------------------------------
    sample_early_min: int = 7
    sample_confirmed_min: int = 14

    # Minimum pairs required even to attempt a correlation.
    min_pairs_for_correlation: int = 3

    # Minimum |correlation| before a candidate is treated as a real pattern.
    min_abs_correlation: float = 0.2

    # ------------------------------------------------------------------
    # Confidence system (section 11).
    # ------------------------------------------------------------------
    conf_weights: tuple[float, float, float, float, float] = (0.30, 0.15, 0.25, 0.15, 0.15)
    #                           sample completeness effect consistency evidence

    def __init__(
        self,
        *,
        sample_early_min: int | None = None,
        sample_confirmed_min: int | None = None,
        min_pairs_for_correlation: int | None = None,
        min_abs_correlation: float | None = None,
        ml_min_samples: int = 30,
        trend_window: int = 14,
    ) -> None:
        if sample_early_min is not None:
            self.sample_early_min = sample_early_min
        if sample_confirmed_min is not None:
            self.sample_confirmed_min = sample_confirmed_min
        if min_pairs_for_correlation is not None:
            self.min_pairs_for_correlation = min_pairs_for_correlation
        if min_abs_correlation is not None:
            self.min_abs_correlation = min_abs_correlation
        self.ml_min_samples = ml_min_samples
        self.trend_window = trend_window
        if self.sample_confirmed_min <= self.sample_early_min:
            raise ValueError("sample_confirmed_min must be > sample_early_min")

    def range_for(self, field: str) -> tuple[float, float]:
        return self.RANGES[field]

    def classify_strength(self, n: int) -> tuple[str, str]:
        """Return ``(strength_key, label)`` for a sample size.

        ``n`` = number of valid paired observations (feature at day t AND
        target at day t+lag).
        """
        if n < self.sample_early_min:
            return "none", "Not enough data"
        if n < self.sample_confirmed_min:
            return "early", "Early pattern"
        return "emerging", "Emerging pattern"

    # Standard instance shared by the app.
    @classmethod
    def default(cls) -> "AnalyticsConfig":
        return cls()