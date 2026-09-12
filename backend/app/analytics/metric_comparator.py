"""Per-metric before/after comparison (Phase 4, analytics module #2).

Pure pandas/numpy maths - no DB, no LLM. Every function takes plain lists of
numeric values (or None for missing) and returns structured comparisons.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass
class MetricComparison:
    metric: str
    baseline_mean: float | None = None
    experiment_mean: float | None = None
    baseline_median: float | None = None
    experiment_median: float | None = None
    difference: float | None = None
    percentage_change: float | None = None
    sample_size: int = 0          # experiment days with a valid value
    valid_observations: int = 0   # baseline invalid days compensated (kept for parity)
    baseline_count: int = 0
    experiment_std: float | None = None
    higher_is_better: bool = True
    direction: str = "no_change"  # improved | worsened | no_change

    @property
    def raw_direction(self) -> str:
        """Direction independent of whether higher/lower is desirable."""
        if self.difference is None:
            return "no_change"
        if self.difference > 1e-9:
            return "increase"
        if self.difference < -1e-9:
            return "decrease"
        return "no_change"


def _valid(values: Sequence[float | None]) -> list[float]:
    return [float(v) for v in values if v is not None and np.isfinite(v)]


def _mean(values: list[float]) -> float | None:
    return float(np.mean(values)) if values else None


def _median(values: list[float]) -> float | None:
    return float(np.median(values)) if values else None


def compare_metric(
    metric: str,
    baseline_values: Sequence[float | None],
    experiment_values: Sequence[float | None],
    higher_is_better: bool = True,
) -> MetricComparison:
    baseline = _valid(baseline_values)
    experiment = _valid(experiment_values)

    b_mean, e_mean = _mean(baseline), _mean(experiment)
    difference = (e_mean - b_mean) if (e_mean is not None and b_mean is not None) else None
    percentage_change = None
    if difference is not None and b_mean and abs(b_mean) > 1e-9:
        percentage_change = (difference / abs(b_mean)) * 100.0

    direction = "no_change"
    if difference is not None and abs(difference) > 1e-9:
        raw = "increase" if difference > 0 else "decrease"
        if higher_is_better:
            direction = "improved" if raw == "increase" else "worsened"
        else:
            direction = "improved" if raw == "decrease" else "worsened"

    return MetricComparison(
        metric=metric,
        baseline_mean=b_mean,
        experiment_mean=e_mean,
        baseline_median=_median(baseline),
        experiment_median=_median(experiment),
        difference=difference,
        percentage_change=percentage_change,
        sample_size=len(experiment),
        baseline_count=len(baseline),
        experiment_std=float(np.std(experiment)) if len(experiment) > 1 else None,
        higher_is_better=higher_is_better,
        direction=direction,
    )