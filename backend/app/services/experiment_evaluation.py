"""Experiment evaluation service (Phase 4, wired into Phase 3 completion).

Loads the user's daily logs for the baseline window and the experiment window,
converts them to numeric series (reusing the Phase 2 categorical maps), runs the
deterministic evaluation pipeline, and persists:

- a human-facing ``ExperimentResult`` (Phase 3)
- per-metric statistics (``ExperimentMetricResult``)
- an evidence assessment (``ExperimentEvidence``)
- a learning candidate (``LearningCandidate``)

Re-evaluating an experiment replaces the previous evaluation (idempotent).
"""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.analytics.config import AnalyticsConfig
from app.analytics.experiment_evaluator import EvaluationResult, evaluate_experiment
from app.analytics.metric_comparator import MetricComparison
from app.core.config import get_settings
from app.models.evaluation import ExperimentEvidence, ExperimentMetricResult, LearningCandidate
from app.models.experiment import Experiment, ExperimentResult
from app.models.daily_log import DailyLog
from app.repositories.daily_log import DailyLogRepository
from app.repositories.experiments import (
    ExperimentDailyLogRepository,
    ExperimentRepository,
    ExperimentResultRepository,
)
from app.services.experiment_templates import meta_for

NUMERIC_METRICS = {
    "sleep_hours", "steps", "active_minutes", "exercise_minutes", "water_liters",
    "screen_time_minutes", "energy", "stress", "mood", "caffeine", "meal_quality",
}
# Categorical fields recorded in experiments that cannot be compared numerically.
_CATEGORICAL = {"sleep_quality"}


class ExperimentEvaluationService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.daily_logs = DailyLogRepository()
        self.experiments_repo = ExperimentRepository()
        self.experiment_logs = ExperimentDailyLogRepository()
        self.results_repo = ExperimentResultRepository()

    # ------------------------------------------------------------------
    def evaluate(self, db: Session, experiment: Experiment) -> EvaluationResult:
        meta = meta_for(experiment.experiment_type)
        track = [m for m in meta.get("track_metrics", []) if m in NUMERIC_METRICS]

        baseline_rows = self._window_rows(
            db, experiment.user_id,
            experiment.start_date - timedelta(days=self.settings.experiment_baseline_window_days),
            experiment.start_date - timedelta(days=1),
        )
        experiment_rows = self._window_rows(db, experiment.user_id, experiment.start_date, experiment.end_date)

        baseline_values = {m: self._series(baseline_rows, m) for m in track}
        experiment_values = {m: self._series(experiment_rows, m) for m in track}

        experiment_logs = self.experiment_logs.list_for_experiment(db, experiment.id)
        target_flags = [row.target_met for row in experiment_logs]

        primary_metric = meta.get("primary_metric", track[0] if track else "energy")

        exp_primary = self._n_valid(experiment_values.get(primary_metric, []))
        base_primary = self._n_valid(baseline_values.get(primary_metric, []))
        exp_completeness = (exp_primary / experiment.duration_days) if experiment.duration_days else 0.0
        baseline_sufficiency = min(1.0, base_primary / self.settings.experiment_min_baseline_days)
        completeness = round(min(exp_completeness, baseline_sufficiency), 4)

        previous = self._prior_similar(db, experiment)

        from app.analytics.evidence_assessor import EvidenceConfig

        result = evaluate_experiment(
            experiment_id=experiment.id,
            experiment_type=experiment.experiment_type,
            baseline_values=baseline_values,
            experiment_values=experiment_values,
            track_metrics=track,
            primary_metric=primary_metric,
            higher_is_better=bool(meta.get("higher_is_better", True)),
            experiment_days_total=experiment.duration_days,
            target_met_flags=target_flags,
            previous_similar_experiments=previous,
            evidence_config=EvidenceConfig.from_settings(self.settings),
            target_definition=meta.get("target_definition", experiment.intervention),
            data_completeness=completeness,
        )
        if result.learning_candidate is not None:
            result.learning_candidate.user_id = experiment.user_id
            result.learning_candidate.source_experiment_id = experiment.id
            result.learning_candidate.pattern_type = meta.get("pattern_type", experiment.experiment_type)
        self._persist(db, experiment, result)
        return result

    # ------------------------------------------------------------------
    def _window_rows(self, db: Session, user_id: int, start: date, end: date) -> list[DailyLog]:
        if start > end:
            return []
        return self.daily_logs.list_in_range(db, user_id, start, end)

    def _series(self, rows: list[DailyLog], metric: str) -> list[float | None]:
        return [_numeric(metric, getattr(row, metric)) for row in rows]

    def _n_valid(self, values: list) -> int:
        return sum(1 for v in values if v is not None)

    def _prior_similar(self, db: Session, experiment: Experiment) -> int:
        from sqlalchemy import select

        count = db.scalars(
            select(Experiment.id).where(
                Experiment.user_id == experiment.user_id,
                Experiment.experiment_type == experiment.experiment_type,
                Experiment.status == "completed",
                Experiment.id != experiment.id,
            )
        )
        return len(list(count))

    # ------------------------------------------------------------------
    def _persist(self, db: Session, experiment: Experiment, result: EvaluationResult) -> None:
        # Replacing the previous evaluation keeps re-runs idempotent.
        for model in (ExperimentResult, ExperimentMetricResult, ExperimentEvidence, LearningCandidate):
            for row in db.scalars(select_all(model, experiment.id)):
                db.delete(row)
        db.flush()

        base_values = {m.metric: {"baseline": m.baseline_mean, "experiment": m.experiment_mean} for m in result.metrics}
        differences = {m.metric: m.difference for m in result.metrics}

        db.add(ExperimentResult(
            experiment_id=experiment.id,
            baseline_values=base_values,
            experiment_values=result.summary,
            differences=differences,
            effect_direction=result.effect_direction,
            sample_size=result.sample_size,
            confidence_level=result.evidence.evidence_level,
            summary=result.summary,
            limitations=result.evidence.limitations,
            learning=_learning_dict(result),
        ))

        for m in result.metrics:
            db.add(_metric_result_row(experiment.id, m))

        db.add(ExperimentEvidence(
            experiment_id=experiment.id,
            data_completeness=result.data_completeness,
            target_adherence=result.adherence.adherence if result.adherence else None,
            consistency_score=result.consistency.score if result.consistency else None,
            evidence_level=result.evidence.evidence_level,
            reason=result.evidence.reason,
            limitations=result.evidence.limitations,
            causality_proven=False,
        ))

        if result.learning_candidate is not None:
            candidate = result.learning_candidate
            db.add(LearningCandidate(
                user_id=candidate.user_id or experiment.user_id,
                experiment_id=experiment.id,
                pattern_type=candidate.pattern_type,
                intervention=candidate.intervention,
                observed_change=candidate.observed_change,
                evidence_level=candidate.evidence_level,
                status="candidate",
                causality_proven=False,
            ))
        db.commit()
        self._trigger_learning_pipeline(db, experiment)

    def _trigger_learning_pipeline(self, db: Session, experiment: Experiment) -> None:
        """Phase 5 hook - kept swappable so Phase 3/4 never depend on Phase 5."""
        try:
            from app.services.personal_learning import PersonalLearningService

            PersonalLearningService().process_candidates_for(db, experiment.user_id, experiment_id=experiment.id)
        except ImportError:
            pass


def _metric_result_row(experiment_id: int, m: MetricComparison) -> ExperimentMetricResult:
    return ExperimentMetricResult(
        experiment_id=experiment_id,
        metric_name=m.metric,
        baseline_mean=m.baseline_mean,
        experiment_mean=m.experiment_mean,
        difference=m.difference,
        percentage_change=m.percentage_change,
        baseline_median=m.baseline_median,
        experiment_median=m.experiment_median,
        sample_size=m.sample_size,
        valid_observations=m.baseline_count,
        direction=m.direction,
    )


def _learning_dict(result: EvaluationResult) -> dict:
    if result.learning_candidate is None:
        return {}
    c = result.learning_candidate
    return {
        "learning_type": c.pattern_type,
        "intervention": c.intervention,
        "observed_change": c.observed_change,
        "evidence_level": c.evidence_level,
        "causality_proven": False,
    }


def select_all(model, experiment_id):
    from sqlalchemy import select

    return select(model).where(model.experiment_id == experiment_id)


def _numeric(metric: str, raw_value) -> float | None:
    """Convert a DailyLog field to its numeric representation (Phase 2 maps)."""
    if raw_value is None:
        return None
    if metric in ("mood",):
        return AnalyticsConfig.MOOD_MAP.get(raw_value)
    if metric == "caffeine":
        return AnalyticsConfig.CAFFEINE_MAP.get(raw_value)
    if metric == "meal_quality":
        return AnalyticsConfig.MEAL_MAP.get(raw_value)
    if metric in _CATEGORICAL:
        return None
    try:
        return float(raw_value)
    except (TypeError, ValueError):
        return None