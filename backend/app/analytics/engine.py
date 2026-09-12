"""Analytics engine orchestrator.

Runs the full Phase 2 pipeline for a single user:

    validated dataset -> personal baseline -> feature engineering ->
    pattern detection -> confidence -> insights -> trends -> (gated) ML model

The engine is pure computation: given a DB session it loads one user's data,
produces an :class:`AnalyticsBundle`, and does NOT write anything. Persistence
is handled by the repository / service layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.analytics.baseline import UserBaseline, compute_baseline
from app.analytics.config import AnalyticsConfig
from app.analytics.dataset import DataQualityReport, Dataset, build_user_dataset
from app.analytics.features import add_features
from app.analytics.insights import InsightGenerator, InsightResult
from app.analytics.ml import MLResult, PersonalWellbeingModel
from app.analytics.patterns import PatternResult, run_pattern_detection
from app.analytics.stats import TrendsResult, compute_trends


@dataclass
class AnalyticsBundle:
    dataset: Dataset = field(default_factory=Dataset)
    quality: DataQualityReport = field(default_factory=DataQualityReport)
    baseline: UserBaseline = field(default_factory=UserBaseline)
    feature_df: object = None
    patterns: list[PatternResult] = field(default_factory=list)
    insights: list[InsightResult] = field(default_factory=list)
    trends: TrendsResult = field(default_factory=TrendsResult)
    ml: MLResult = field(default_factory=MLResult)

    @property
    def has_any_pattern(self) -> bool:
        return any(p.has_pattern for p in self.patterns)


class AnalyticsEngine:
    def __init__(self, config: AnalyticsConfig | None = None) -> None:
        self.config = config or AnalyticsConfig.default()

    def run(self, db: Session, user_id: int) -> AnalyticsBundle:
        dataset = build_user_dataset(db, user_id, self.config)
        bundle = AnalyticsBundle(dataset=dataset, quality=dataset.quality)

        if dataset.empty:
            return bundle

        baseline = compute_baseline(dataset.df, dataset.quality)
        bundle.baseline = baseline

        feature_df = add_features(dataset.df, baseline, self.config)
        bundle.feature_df = feature_df

        bundle.patterns = run_pattern_detection(dataset.df, baseline, self.config)
        generator = InsightGenerator()
        bundle.insights = [
            generator.generate(p) for p in bundle.patterns if p.has_pattern
        ]
        bundle.trends = compute_trends(dataset.df, baseline, self.config)
        bundle.ml = PersonalWellbeingModel(self.config).run(feature_df)
        return bundle