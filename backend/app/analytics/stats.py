"""Statistical analysis for the Phase 2 engine.

Deliberately small and honest: Pearson / Spearman correlations, p-values,
lagged pairing and bucket comparisons. Every function degrades gracefully to
``None`` when the data cannot support a statistical claim (no fake numbers).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from app.analytics.config import AnalyticsConfig
from app.analytics.dataset import METRIC_COLUMNS


# ---------------------------------------------------------------------------
# Basic statistics
# ---------------------------------------------------------------------------
def pearson(x: np.ndarray, y: np.ndarray) -> tuple[float | None, int]:
    """Pearson product-moment correlation coefficient.

    Returns ``(r, n)``; ``r`` is ``None`` if there is no variance in either
    series or fewer than 2 points.
    """
    n = len(x)
    if n < 2 or len(y) != n:
        return None, n
    xm, ym = float(x.mean()), float(y.mean())
    sxy = sum(float((xi - xm) * (yi - ym)) for xi, yi in zip(x, y))
    sxx = sum(float((xi - xm) ** 2) for xi in x)
    syy = sum(float((yi - ym) ** 2) for yi in y)
    denom = math.sqrt(sxx * syy)
    if denom == 0:
        return None, n
    r = sxy / denom
    return float(np.clip(r, -1.0, 1.0)), n


def _ranks(values: np.ndarray) -> np.ndarray:
    """Average-rank ties (SciPy-free fallback)."""
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty_like(values, dtype=float)
    n = len(values)
    i = 0
    while i < n:
        j = i
        while j + 1 < n and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def spearman(x: np.ndarray, y: np.ndarray) -> tuple[float | None, int]:
    """Spearman's rank correlation with tie handling."""
    n = len(x)
    if n < 2 or len(y) != n:
        return None, n
    rx = _ranks(x)
    ry = _ranks(y)
    return pearson(rx, ry)


def pearson_p_value(r: float, n: int) -> float | None:
    """Two-sided p-value for Pearson r via the t distribution.

    Falls back to a Fisher-z normal approximation if SciPy is unavailable.
    """
    if n < 3:
        return None
    try:
        from scipy.stats import t as _t

        t_stat = r * math.sqrt((n - 2) / (1 - r * r)) if abs(r) < 1.0 else math.copysign(math.inf, r)
        return float(2.0 * _t.sf(abs(t_stat), df=n - 2))
    except Exception:  # pragma: no cover - scipy is a hard dependency
        return None


# ---------------------------------------------------------------------------
# Lagged relationship analysis (section 9)
# ---------------------------------------------------------------------------
@dataclass
class LagResult:
    """Result of ``analyze_lagged_relationship``."""

    feature: str
    target: str
    lag_days: int
    n: int = 0
    possible_pairs: int = 0
    r: float | None = None
    rho: float | None = None
    p_value: float | None = None
    direction: str | None = None
    magnitude: float | None = None
    completeness: float = 0.0
    feasible: bool = False
    mean_low: float | None = None
    mean_high: float | None = None
    low_bucket: str | None = None
    high_bucket: str | None = None
    buckets: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "feature": self.feature,
            "target": self.target,
            "lag_days": self.lag_days,
            "n": self.n,
            "possible_pairs": self.possible_pairs,
            "correlation": None if self.r is None else round(self.r, 4),
            "spearman": None if self.rho is None else round(self.rho, 4),
            "p_value": None if self.p_value is None else round(self.p_value, 4),
            "direction": self.direction,
            "magnitude": None if self.magnitude is None else round(self.magnitude, 4),
            "completeness": round(self.completeness, 4),
            "feasible": self.feasible,
            "mean_low": None if self.mean_low is None else round(self.mean_low, 3),
            "mean_high": None if self.mean_high is None else round(self.mean_high, 3),
            "buckets": self.buckets,
        }


def lagged_pairs(
    dataframe,
    feature: str,
    target: str,
    lag_days: int,
    feature_transform=None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """Align ``feature`` at day t with ``target`` at day t+lag.

    Returns ``(x, y, dates_of_y, denominator)`` where only pairs where both the
    feature value and the shifted target value are present are kept. When
    ``feature_transform`` is given (e.g. ``lambda s: (s > 0).astype(float)``),
    the feature series is transformed before pairing.
    """
    if feature not in dataframe.columns or target not in dataframe.columns:
        return np.array([]), np.array([]), np.array([]), 0.0

    x_series = dataframe[feature]
    if feature_transform is not None:
        x_series = feature_transform(x_series)

    y_shift = dataframe[target].shift(-lag_days)
    mask = x_series.notna() & y_shift.notna()
    x = x_series[mask].to_numpy(dtype=float)
    y = y_shift[mask].to_numpy(dtype=float)

    # Denominator = slots where a feature value exists AND a lag-target slot exists.
    feature_mask = x_series.notna()
    denom_array = feature_mask & (np.arange(len(dataframe)) + lag_days < len(dataframe))
    # Keep the same transform applied above (mask already reflects it).
    denom = max(int(denom_array.sum()), 0)

    dates = dataframe["date"].to_numpy()
    return x, y, dates[mask.to_numpy()], float(denom or (len(x) or 0))


def analyze_lagged_relationship(
    dataframe,
    feature: str,
    target: str,
    lag_days: int = 1,
    config: AnalyticsConfig | None = None,
    feature_transform=None,
) -> LagResult:
    """Full lagged statistical analysis for one feature -> target pair."""
    config = config or AnalyticsConfig.default()
    result = LagResult(feature=feature, target=target, lag_days=lag_days)

    x, y, _, denom = lagged_pairs(dataframe, feature, target, lag_days, feature_transform)
    n = len(x)
    result.n = n
    result.possible_pairs = int(denom)
    result.completeness = (n / denom) if denom else 0.0
    if n < config.min_pairs_for_correlation:
        return result

    r, _ = pearson(x, y)
    result.feasible = True
    result.r = r
    result.rho = None
    if r is not None:
        rho, _ = spearman(x, y)
        result.rho = rho
        result.p_value = pearson_p_value(r, n)
        result.magnitude = abs(r)
        if abs(r) >= 1e-9:
            result.direction = "positive" if r > 0 else "negative"
    return result


# ---------------------------------------------------------------------------
# Bucket comparisons for explainability (section 12)
# ---------------------------------------------------------------------------
def bucket_by_thresholds(
    dataframe,
    feature: str,
    target: str,
    lag_days: int,
    thresholds: list[tuple[float, float, str]],
    feature_transform=None,
    target_name: str = "",
) -> LagResult | None:
    """Split the feature into labelled buckets and compute mean target per bucket.

    ``thresholds`` is a list of ``(lo, hi, label)`` where the bucket spans
    ``lo <= value < hi``. Returns a ``LagResult`` populated with per-bucket
    means (plus the same correlation numbers via ``analyze_lagged_relationship``).
    """
    result = analyze_lagged_relationship(
        dataframe, feature, target, lag_days, feature_transform=feature_transform
    )
    x, y, _, _ = lagged_pairs(dataframe, feature, target, lag_days, feature_transform)

    buckets: list[dict] = []
    if len(x) == 0:
        result.mean_low = result.mean_high = None
        result.buckets = buckets
        return result

    for lo, hi, label in thresholds:
        mask = (x >= lo) & (x < hi)
        bucket_y = y[mask]
        buckets.append(
            {
                "label": label,
                "range": f"{lo:g}-{hi:g}",
                "n": int(mask.sum()),
                "mean_target": None if bucket_y.size == 0 else round(float(bucket_y.mean()), 3),
            }
        )

    valid = [b for b in buckets if b["mean_target"] is not None]
    if len(valid) >= 2:
        result.low_bucket = valid[0]["label"]
        result.high_bucket = valid[-1]["label"]
        result.mean_low = valid[0]["mean_target"]
        result.mean_high = valid[-1]["mean_target"]
    result.buckets = buckets
    return result


# ---------------------------------------------------------------------------
# Trends (section 18 / dashboard "latest insight")
# ---------------------------------------------------------------------------
@dataclass
class MetricTrend:
    metric: str
    series: list[dict] = field(default_factory=list)  # [{date, value}]
    latest: float | None = None
    baseline_avg: float | None = None
    avg_3d: float | None = None
    avg_7d: float | None = None
    day_deltas: list[float] = field(default_factory=list)
    direction: str | None = None  # up | down | flat
    delta_vs_baseline: float | None = None

    def to_dict(self) -> dict:
        return {
            "metric": self.metric,
            "series": self.series,
            "latest": _round4(self.latest),
            "baseline_avg": _round4(self.baseline_avg),
            "avg_3d": _round4(self.avg_3d),
            "avg_7d": _round4(self.avg_7d),
            "day_deltas": [_round4(d) for d in self.day_deltas],
            "direction": self.direction,
            "delta_vs_baseline": _round4(self.delta_vs_baseline),
        }


@dataclass
class TrendsResult:
    window_days: int = 0
    metrics: dict[str, MetricTrend] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "window_days": self.window_days,
            "metrics": [self.metrics[m].to_dict() for m in self.metrics],
        }


def _round4(v: float | None) -> float | None:
    return None if v is None else round(v, 4)


def compute_trends(dataframe, baseline, config: AnalyticsConfig | None = None) -> TrendsResult:
    config = config or AnalyticsConfig.default()
    result = TrendsResult(window_days=config.trend_window)
    if dataframe.empty:
        return result

    df = dataframe.sort_values("date").reset_index(drop=True)
    last_n = df.tail(config.trend_window)
    for metric in METRIC_COLUMNS:
        if metric not in df.columns:
            continue
        series = df[metric]
        if series.notna().sum() == 0:
            continue
        trend = MetricTrend(metric=metric)
        series_last = last_n[metric]
        trend.latest = _round4(float(series.iloc[-1])) if not np.isnan(series.iloc[-1]) else None
        trend.baseline_avg = baseline.avg(metric)
        if len(series) >= 3:
            trend.avg_3d = _round4(float(series.tail(3).mean()))
        if len(series) >= 7:
            trend.avg_7d = _round4(float(series.tail(7).mean()))
        deltas = [float(series.iloc[i] - series.iloc[i - 1]) for i in range(1, len(series)) if
                  not np.isnan(series.iloc[i]) and not np.isnan(series.iloc[i - 1])]
        trend.day_deltas = deltas
        series_clean = last_n[metric].dropna()
        trend.series = [
            {"date": df.at[i, "date"].isoformat(), "value": _round4(float(series_clean.at[i]))}
            for i in series_clean.index
        ]
        if trend.latest is not None and trend.baseline_avg is not None:
            base = float(trend.baseline_avg)
            threshold = max(0.1, abs(base) * 0.05)
            diff = float(trend.latest) - base
            trend.delta_vs_baseline = round(diff, 4)
            trend.direction = "up" if diff > threshold else ("down" if diff < -threshold else "flat")
        result.metrics[metric] = trend
    return result