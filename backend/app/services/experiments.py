"""Experiment orchestration service (Phase 3, sections 6-9 + section 11).

Exposes the business actions: start, daily log, complete, cancel, and read
paths. Metric values recorded during an experiment are written into the user's
EXISTING Phase 1 daily log for the same date, so the experiment analysis and
the pattern engine always agree on the underlying numbers.

Missing data stays missing - we never fabricate a check-in or a metric value.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analytics.experiment_evaluator import EvaluationResult
from app.core.errors import BadRequestError, ConflictError, NotFoundError
from app.models.daily_log import DailyLog
from app.models.evaluation import ExperimentEvidence, ExperimentMetricResult
from app.models.experiment import Experiment
from app.models.user import User
from app.repositories.daily_log import DailyLogRepository
from app.repositories.experiments import (
    ExperimentDailyLogRepository,
    ExperimentRepository,
    ExperimentResultRepository,
)
from app.schemas.experiment import (
    ExperimentResultResponse,
    MetricComparisonResponse,
)
from app.services.experiment_evaluation import ExperimentEvaluationService
from app.services.experiment_templates import (
    TEMPLATE_META,
    get_template,
)

# Fields that may be written into the user's daily log from an experiment check-in.
ALLOWED_METRIC_KEYS = {
    "sleep_hours", "steps", "active_minutes", "exercise_minutes", "water_liters",
    "meal_quality", "screen_time_minutes", "late_night_screen", "caffeine",
    "mood", "energy", "stress", "sleep_quality", "exercise_level",
}


class ExperimentService:
    def __init__(self) -> None:
        self.repo = ExperimentRepository()
        self.logs = ExperimentDailyLogRepository()
        self.results = ExperimentResultRepository()
        self.daily_logs = DailyLogRepository()
        self.evaluation_service = ExperimentEvaluationService()

    # --- write actions ---------------------------------------------------------
    def start(self, db: Session, user: User, experiment_type: str) -> Experiment:
        if self.repo.get_active(db, user.id) is not None:
            raise ConflictError(
                "You already have an active experiment. Finish or cancel it before starting another."
            )
        template = get_template(db, experiment_type)
        today = date.today()

        exp = self.repo.create(
            db,
            user.id,
            pattern_id=TEMPLATE_META.get(experiment_type, {}).get("pattern_type", experiment_type),
            experiment_type=template.experiment_type,
            title=template.title,
            hypothesis=template.hypothesis_template,
            intervention=template.intervention,
            duration_days=template.duration_days,
            start_date=today,
            end_date=today + timedelta(days=template.duration_days - 1),
            status="active",
        )
        return exp

    def record_daily_log(self, db: Session, user: User, experiment_id: int, payload) -> object:
        exp = self.repo.get_owned(db, user.id, experiment_id)
        if exp.status == "completed":
            raise ConflictError("This experiment is already completed - you can no longer add check-ins.")
        if exp.status not in ("active", "paused"):
            raise BadRequestError("Only an active experiment accepts daily check-ins.")

        log_date = payload.date or date.today()
        if not (exp.start_date <= log_date <= exp.end_date):
            raise BadRequestError(
                f"This date is outside the experiment window ({exp.start_date} to {exp.end_date})."
            )
        day_number = (log_date - exp.start_date).days + 1

        row = self.logs.upsert(
            db,
            exp.id,
            log_date,
            completed=payload.completed,
            target_met=payload.target_met,
            notes=payload.notes,
            day_number=day_number,
        )

        if payload.metrics:
            self._write_daily_log_metrics(db, user.id, log_date, payload.metrics)
        return row

    def complete(self, db: Session, user: User, experiment_id: int) -> ExperimentResultResponse:
        exp = self.repo.get_owned(db, user.id, experiment_id)
        if exp.status == "completed":
            raise ConflictError("This experiment has already been completed.")
        if exp.status not in ("active", "paused"):
            raise BadRequestError("Only an active experiment can be completed.")

        self.evaluation_service.evaluate(db, exp)
        exp.status = "completed"
        exp.completed_at = datetime.utcnow()
        db.commit()
        return self.result(db, user, experiment_id)

    def cancel(self, db: Session, user: User, experiment_id: int) -> Experiment:
        exp = self.repo.get_owned(db, user.id, experiment_id)
        if exp.status != "active":
            raise BadRequestError("Only an active experiment can be cancelled.")
        exp.status = "cancelled"
        db.commit()
        db.refresh(exp)
        return exp

    # --- read paths ------------------------------------------------------------
    def active(self, db: Session, user_id: int) -> Experiment | None:
        return self.repo.get_active(db, user_id)

    def detail(self, db: Session, user: User, experiment_id: int):
        exp = self.repo.get_owned(db, user.id, experiment_id)
        daily_logs = self.logs.list_for_experiment(db, experiment_id)
        today = date.today()
        days_into = min(max((today - exp.start_date).days + 1, 1), exp.duration_days)
        progress = min(100, round(days_into / exp.duration_days * 100)) if exp.duration_days else 0
        return exp, daily_logs, today, days_into, progress

    def history(self, db: Session, user: User, user_id: int) -> list[tuple[Experiment, ExperimentResultResponse | None]]:
        experiments = self.repo.list_by_user(db, user_id, status=None)
        items = []
        for exp in experiments:
            if exp.status not in ("completed", "cancelled"):
                continue
            row = self._result_row(db, exp.id)
            result = self._build_response(db, exp, row) if row is not None else None
            items.append((exp, result))
        return items

    def result(self, db: Session, user: User, experiment_id: int) -> ExperimentResultResponse:
        exp = self.repo.get_owned(db, user.id, experiment_id)
        row = self._result_row(db, exp.id)
        if row is None:
            raise NotFoundError("This experiment has not been evaluated yet.")
        return self._build_response(db, exp, row)

    # --- internals ---------------------------------------------------------------
    def _write_daily_log_metrics(self, db: Session, user_id: int, log_date: date, metrics: dict) -> None:
        fields = {k: v for k, v in metrics.items() if k in ALLOWED_METRIC_KEYS and v is not None}
        if not fields:
            return
        existing = self.daily_logs.get_for_user_date(db, user_id, log_date)
        if existing is None:
            self.daily_logs.create(db, user_id, date=log_date, **fields)
        else:
            self.daily_logs.update(db, user_id, log_date, **fields)

    def _result_row(self, db: Session, experiment_id: int):
        return self.results.get_by_experiment(db, experiment_id)

    def _build_response(self, db: Session, exp: Experiment, row) -> ExperimentResultResponse:
        evidence = db.scalars(
            select(ExperimentEvidence).where(ExperimentEvidence.experiment_id == exp.id)
        ).first()
        metric_rows = list(
            db.scalars(
                select(ExperimentMetricResult)
                .where(ExperimentMetricResult.experiment_id == exp.id)
                .order_by(ExperimentMetricResult.id)
            )
        )
        metrics = [
            MetricComparisonResponse(
                metric=m.metric_name,
                baseline_mean=m.baseline_mean,
                experiment_mean=m.experiment_mean,
                baseline_median=m.baseline_median,
                experiment_median=m.experiment_median,
                difference=m.difference,
                percentage_change=m.percentage_change,
                sample_size=m.sample_size,
                valid_observations=m.valid_observations,
                direction=m.direction,
            )
            for m in metric_rows
        ]

        exp_logs = self.logs.list_for_experiment(db, exp.id)
        met = sum(1 for log in exp_logs if log.target_met is True)
        adherence_text = f"Target met on {met} of {exp.duration_days} days." if exp.duration_days else None

        return ExperimentResultResponse(
            experiment_id=exp.id,
            status=exp.status or "completed",
            metrics=metrics,
            data_completeness=(evidence.data_completeness if evidence else 0.0),
            sample_size=(row.sample_size or 0),
            target_adherence=(evidence.target_adherence if evidence else None),
            target_adherence_text=adherence_text,
            consistency_score=(evidence.consistency_score if evidence else None),
            evidence_level=(row.confidence_level or "INSUFFICIENT"),
            causality_proven=False,
            summary=row.summary or "",
            limitations=row.limitations or "",
            learning=row.learning or {},
        )