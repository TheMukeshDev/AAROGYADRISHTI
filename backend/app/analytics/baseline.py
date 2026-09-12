"""Personal baseline calculation (Phase 2, section 5).

A user's baseline is their OWN historical "normal": average, median, min, max
and variability for each tracked metric plus data completeness. It is NEVER
compared against population or medical thresholds.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.analytics.dataset import METRIC_COLUMNS, DataQualityReport


@dataclass
class MetricStats:
    field: str
    count: int = 0
    avg: float | None = None
    median: float | None = None
    min: float | None = None
    max: float | None = None
    std: float | None = None
    completeness: float = 0.0

    def to_dict(self) -> dict:
        return {
            "field": self.field,
            "count": self.count,
            "avg": _round3(self.avg),
            "median": _round3(self.median),
            "min": _round3(self.min),
            "max": _round3(self.max),
            "std": _round3(self.std),
            "completeness": round(self.completeness, 4),
        }


@dataclass
class UserBaseline:
    data_days: int = 0
    overall_completeness: float = 0.0
    metrics: dict[str, MetricStats] = field(default_factory=dict)

    # Convenience accessors used by insights / explainability.
    def avg(self, field: str) -> float | None:
        return self.metrics.get(field).avg if field in self.metrics else None

    def complement(self, field: str) -> float:
        return self.metrics.get(field).completeness if field in self.metrics else 0.0

    @property
    def avg_sleep(self) -> float | None:
        return self.avg("sleep_hours")

    @property
    def avg_energy(self) -> float | None:
        return self.avg("energy")

    @property
    def avg_stress(self) -> float | None:
        return self.avg("stress")

    @property
    def avg_mood(self) -> float | None:
        return self.avg("mood")

    def to_dict(self) -> dict:
        return {
            "data_days": self.data_days,
            "overall_completeness": round(self.overall_completeness, 4),
            "metrics": [self.metrics[f].to_dict() for f in METRIC_COLUMNS if f in self.metrics],
        }


def _round3(value: float | None) -> float | None:
    return None if value is None else round(value, 3)


def compute_baseline(dataframe, quality: DataQualityReport) -> UserBaseline:
    """Compute a personal baseline from a validated analytics DataFrame.

    ``dataframe`` must contain the validated numeric columns (from
    ``build_user_dataset``).
    """
    baseline = UserBaseline(data_days=len(dataframe.index), overall_completeness=quality.completeness)

    if dataframe.empty:
        return baseline

    for col in METRIC_COLUMNS:
        if col not in dataframe.columns:
            continue
        series = dataframe[col].dropna()
        n = int(series.count())
        if n == 0:
            baseline.metrics[col] = MetricStats(field=col, count=0, completeness=0.0)
            continue
        std = float(series.std(ddof=1)) if n >= 2 else None
        baseline.metrics[col] = MetricStats(
            field=col,
            count=n,
            avg=float(series.mean()),
            median=float(series.median()),
            min=float(series.min()),
            max=float(series.max()),
            std=std,
            completeness=quality.per_field_completeness.get(col, n / len(dataframe.index)),
        )
    return baseline