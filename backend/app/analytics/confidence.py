"""Explainable confidence system (Phase 2, section 11).

Confidence is never an arbitrary AI score. It is a weighted combination of:

- **sample factor**    : how many observations (relative to config thresholds)
- **completeness**     : fraction of possible paired observations that existed
- **effect strength**  : |correlation| relative to 0.5
- **consistency**      : agreement of the pattern in the first vs second half
- **statistical**      : p-value proximity to 0.05

A HIGH confidence still never means "X causes Y" - it means "this association is
consistently observed in this user's own data". See ``explain.py`` for the
cautious-language boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from app.analytics.config import AnalyticsConfig
from app.analytics.stats import LagResult, pearson


@dataclass
class ConfidenceResult:
    score: float = 0.0
    level: str = "none"  # none | low | moderate | high
    strength: str = "none"  # none | early | emerging
    strength_label: str = "Not enough data"
    factors: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "score": round(self.score, 4),
            "level": self.level,
            "strength": self.strength,
            "strength_label": self.strength_label,
            "factors": {k: round(v, 4) for k, v in self.factors.items()} if self.factors else {},
        }


def _first_second_half_correlation(x: np.ndarray, y: np.ndarray) -> tuple[float | None, float | None]:
    n = len(x)
    if n < 6:
        return None, None
    half = n // 2
    r1, _ = pearson(x[:half], y[:half])
    r2, _ = pearson(x[half:], y[half:])
    return r1, r2


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return float(min(max(v, lo), hi))


class ConfidenceEngine:
    def __init__(self, config: AnalyticsConfig | None = None) -> None:
        self.config = config or AnalyticsConfig.default()

    def compute(self, lag: LagResult) -> ConfidenceResult:
        cfg = self.config
        n = lag.n
        strength, strength_label = cfg.classify_strength(n)
        factors: dict[str, float] = {}

        if lag.r is None or lag.n < cfg.sample_early_min:
            factors = {"sample": 0.0, "completeness": lag.completeness, "effect": 0.0,
                       "consistency": 0.0, "evidence": 0.0}
            return ConfidenceResult(score=0.0, level="none", strength=strength,
                                    strength_label=strength_label, factors=factors)

        sample_factor = _clamp((n - cfg.sample_early_min) / max(cfg.sample_confirmed_min - cfg.sample_early_min, 1))
        completeness_factor = float(lag.completeness)
        effect_factor = _clamp(abs(lag.r) / 0.5)

        r1, r2 = _first_second_half_correlation(*_xy_from_lag(lag))
        if r1 is not None and r2 is not None:
            consistency_factor = _clamp(1.0 - abs(r1 - r2) / 2.0)
        elif lag.rho is not None and lag.r is not None and abs(abs(lag.rho) - abs(lag.r)) < 0.25:
            consistency_factor = 0.7  # pearson/spearman agree; too few points for halves
        else:
            consistency_factor = 0.5

        if lag.p_value is None:
            evidence_factor = 0.5
        else:
            evidence_factor = _clamp(1.0 - lag.p_value / 0.05)

        factors = {
            "sample": round(sample_factor, 4),
            "completeness": round(completeness_factor, 4),
            "effect": round(effect_factor, 4),
            "consistency": round(consistency_factor, 4),
            "evidence": round(evidence_factor, 4),
        }

        w_sample, w_comp, w_effect, w_cons, w_ev = cfg.conf_weights
        score = (
            w_sample * sample_factor
            + w_comp * completeness_factor
            + w_effect * effect_factor
            + w_cons * consistency_factor
            + w_ev * evidence_factor
        )
        if score >= 0.62:
            level = "high"
        elif score >= 0.40:
            level = "moderate"
        else:
            level = "low"

        return ConfidenceResult(score=score, level=level, strength=strength,
                                strength_label=strength_label, factors=factors)


def _xy_from_lag(lag: LagResult) -> tuple[np.ndarray, np.ndarray]:
    """Best-effort reconstruction of the pair arrays for consistency checks.

    ``LagResult`` intentionally keeps only summary stats, so when the caller
    wants half-split consistency the engine attaches the raw series via the
    ``_x`` / ``_y`` ephemeral attributes set by the analyzer.
    """
    x = getattr(lag, "_x", None)
    y = getattr(lag, "_y", None)
    if x is not None and y is not None:
        return x, y
    return np.array([]), np.array([])