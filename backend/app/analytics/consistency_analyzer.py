"""Consistency analysis (Phase 4, analytics module #3).

Measures whether the day-to-day behaviour during the experiment was consistent
with the overall observed change - NOT whether the change was caused by the
intervention.

``consistency_score`` is in [0, 1]: 1.0 = every experiment day moved in the
same direction as the average change with low day-to-day scatter.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass
class ConsistencyResult:
    score: float
    direction_bias: float      # fraction of days agreeing with the mean change
    stability: float           # 1 - cv of |daily deltas|, clamped [0, 1]
    mean_daily_delta: float | None
    n_valid_days: int
    verdict: str               # consistent | variable | undefined


def analyze_consistency(
    baseline_mean: float | None,
    experiment_values: Sequence[float | None],
) -> ConsistencyResult:
    valid = [float(v) for v in experiment_values if v is not None and np.isfinite(v)]
    if baseline_mean is None or len(valid) < 1:
        return ConsistencyResult(score=0.0, direction_bias=0.0, stability=0.0,
                                 mean_daily_delta=None, n_valid_days=0, verdict="undefined")

    deltas = np.array(valid) - baseline_mean
    mean_delta = float(np.mean(deltas))
    if abs(mean_delta) <= 1e-9:
        return ConsistencyResult(score=1.0, direction_bias=1.0, stability=1.0,
                                 mean_daily_delta=0.0, n_valid_days=len(deltas), verdict="consistent")

    target_sign = 1.0 if mean_delta > 0 else -1.0
    direction_bias = float(np.mean(np.sign(deltas) == target_sign))

    # Stability: low relative scatter of absolute deviations.
    abs_deltas = np.abs(deltas)
    cv = float(np.std(abs_deltas) / (np.mean(abs_deltas) + 1e-9)) if len(abs_deltas) > 1 else 0.0
    stability = float(np.clip(1.0 - cv, 0.0, 1.0))

    score = float(np.clip(0.6 * direction_bias + 0.4 * stability, 0.0, 1.0))
    verdict = "consistent" if score >= 0.6 else "variable"
    return ConsistencyResult(
        score=round(score, 4), direction_bias=round(direction_bias, 4),
        stability=round(stability, 4), mean_daily_delta=round(mean_delta, 4),
        n_valid_days=len(deltas), verdict=verdict,
    )