"""Experiment + evaluation endpoints (Phase 3 and Phase 4).

Every endpoint validates authentication (``CurrentUser``) and ownership via the
repositories - an experiment can only ever be read or mutated by its owner.
"""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core.errors import ConflictError, NotFoundError
from app.models.evaluation import ExperimentEvidence, ExperimentMetricResult, LearningCandidate
from app.schemas.common import Message
from app.schemas.experiment import (
    AcceptRejectResponse,
    ActiveExperimentResponse,
    ExperimentDailyLogRequest,
    ExperimentDailyLogResponse,
    ExperimentDetailResponse,
    ExperimentEvidenceResponse,
    ExperimentHistoryItem,
    ExperimentResponse,
    ExperimentResultResponse,
    ExperimentStartRequest,
    ExperimentTemplateResponse,
    LearningCandidateListResponse,
    LearningCandidateResponse,
    MetricComparisonResponse,
    RecommendationResponse,
)
from app.services import experiment_recommendation
from app.services.experiment_evaluation import ExperimentEvaluationService
from app.services.experiment_templates import list_active_templates
from app.services.experiments import ExperimentService

router = APIRouter(tags=["experiments"])
_service = ExperimentService()
_evaluation = ExperimentEvaluationService()


@router.get("/experiments/recommended", response_model=RecommendationResponse)
def recommended(db: DbSession, user: CurrentUser):
    return experiment_recommendation.recommend(db, user)


@router.post("/experiments", response_model=ExperimentResponse, status_code=201)
def start_experiment(payload: ExperimentStartRequest, db: DbSession, user: CurrentUser):
    return _service.start(db, user, payload.experiment_type)


@router.get("/experiments/active", response_model=ActiveExperimentResponse)
def active_experiment(db: DbSession, user: CurrentUser):
    return ActiveExperimentResponse(experiment=_service.active(db, user.id))


@router.get("/experiments/history", response_model=list[ExperimentHistoryItem])
def experiment_history(db: DbSession, user: CurrentUser):
    items = _service.history(db, user, user.id)
    return [
        ExperimentHistoryItem(
            experiment=ExperimentResponse.model_validate(exp),
            result=result,
        )
        for exp, result in items
    ]


@router.get("/experiments/{experiment_id}", response_model=ExperimentDetailResponse)
def experiment_detail(experiment_id: int, db: DbSession, user: CurrentUser):
    exp, logs, today, days_into, progress = _service.detail(db, user, experiment_id)
    return ExperimentDetailResponse(
        experiment=ExperimentResponse.model_validate(exp),
        daily_logs=[ExperimentDailyLogResponse.model_validate(log) for log in logs],
        target=exp.intervention,
        today=today,
        days_into=days_into,
        progress_percent=progress,
    )


@router.post("/experiments/{experiment_id}/daily-log", response_model=ExperimentDailyLogResponse)
def record_daily_log(experiment_id: int, payload: ExperimentDailyLogRequest, db: DbSession, user: CurrentUser):
    row = _service.record_daily_log(db, user, experiment_id, payload)
    return ExperimentDailyLogResponse.model_validate(row)


@router.post("/experiments/{experiment_id}/complete", response_model=ExperimentResultResponse)
def complete_experiment(experiment_id: int, db: DbSession, user: CurrentUser):
    return _service.complete(db, user, experiment_id)


@router.post("/experiments/{experiment_id}/cancel", response_model=ExperimentResponse)
def cancel_experiment(experiment_id: int, db: DbSession, user: CurrentUser):
    return _service.cancel(db, user, experiment_id)


@router.get("/experiments/{experiment_id}/result", response_model=ExperimentResultResponse)
def experiment_result(experiment_id: int, db: DbSession, user: CurrentUser):
    return _service.result(db, user, experiment_id)


# --- Phase 4 evaluation endpoints -------------------------------------------
@router.post("/experiments/{experiment_id}/evaluate", response_model=ExperimentResultResponse)
def evaluate_experiment(experiment_id: int, db: DbSession, user: CurrentUser):
    exp = _service.repo.get_owned(db, user.id, experiment_id)
    if exp.status != "completed":
        raise ConflictError("Only a completed experiment can be evaluated.")
    result = _evaluation.evaluate(db, exp)
    return _service.result(db, user, experiment_id)


@router.get("/experiments/{experiment_id}/evaluation", response_model=ExperimentResultResponse)
def evaluation(experiment_id: int, db: DbSession, user: CurrentUser):
    return _service.result(db, user, experiment_id)


@router.get("/experiments/{experiment_id}/metrics", response_model=list[MetricComparisonResponse])
def evaluation_metrics(experiment_id: int, db: DbSession, user: CurrentUser):
    exp = _service.repo.get_owned(db, user.id, experiment_id)
    rows = list(
        db.scalars(
            select(ExperimentMetricResult)
            .where(ExperimentMetricResult.experiment_id == exp.id)
            .order_by(ExperimentMetricResult.id)
        )
    )
    return [
        MetricComparisonResponse(
            metric=r.metric_name,
            baseline_mean=r.baseline_mean,
            experiment_mean=r.experiment_mean,
            baseline_median=r.baseline_median,
            experiment_median=r.experiment_median,
            difference=r.difference,
            percentage_change=r.percentage_change,
            sample_size=r.sample_size,
            valid_observations=r.valid_observations,
            direction=r.direction,
        )
        for r in rows
    ]


@router.get("/experiments/{experiment_id}/evidence", response_model=ExperimentEvidenceResponse)
def evaluation_evidence(experiment_id: int, db: DbSession, user: CurrentUser):
    exp = _service.repo.get_owned(db, user.id, experiment_id)
    row = db.scalars(
        select(ExperimentEvidence).where(ExperimentEvidence.experiment_id == exp.id)
    ).first()
    if row is None:
        raise NotFoundError("This experiment has not been evaluated yet.")
    return row


# --- Learning candidates (Phase 4) ------------------------------------------
@router.get("/experiments/{experiment_id}/learning-candidate", response_model=LearningCandidateResponse | None)
def learning_candidate(experiment_id: int, db: DbSession, user: CurrentUser):
    exp = _service.repo.get_owned(db, user.id, experiment_id)
    return db.scalars(
        select(LearningCandidate).where(LearningCandidate.experiment_id == exp.id)
    ).first()


@router.get("/learning-candidates", response_model=LearningCandidateListResponse)
def list_learning_candidates(db: DbSession, user: CurrentUser):
    rows = list(
        db.scalars(
            select(LearningCandidate)
            .where(LearningCandidate.user_id == user.id)
            .order_by(LearningCandidate.created_at.desc())
        )
    )
    return LearningCandidateListResponse(candidates=[LearningCandidateResponse.model_validate(r) for r in rows])


def _candidate_owned(db, user_id, candidate_id) -> LearningCandidate:
    row = db.scalars(
        select(LearningCandidate).where(
            LearningCandidate.id == candidate_id, LearningCandidate.user_id == user_id
        )
    ).first()
    if row is None:
        raise NotFoundError("Learning candidate not found.")
    return row


@router.post("/learning-candidates/{candidate_id}/accept", response_model=AcceptRejectResponse)
def accept_candidate(candidate_id: int, db: DbSession, user: CurrentUser):
    row = _candidate_owned(db, user.id, candidate_id)
    from app.services.learning_candidates import transition_candidate
    from app.services.personal_learning import PersonalLearningService

    status = transition_candidate(row, "accepted")
    db.flush()
    PersonalLearningService().recalculate_for_key(db, user.id, row.pattern_type, row.intervention)
    db.commit()
    return AcceptRejectResponse(status=status, message="Learning candidate accepted.")


@router.post("/learning-candidates/{candidate_id}/reject", response_model=AcceptRejectResponse)
def reject_candidate(candidate_id: int, db: DbSession, user: CurrentUser):
    row = _candidate_owned(db, user.id, candidate_id)
    from app.services.learning_candidates import transition_candidate
    from app.services.personal_learning import PersonalLearningService

    status = transition_candidate(row, "rejected")
    db.flush()
    PersonalLearningService().recalculate_for_key(db, user.id, row.pattern_type, row.intervention)
    db.commit()
    return AcceptRejectResponse(status=status, message="Learning candidate rejected.")


@router.get("/experiment-templates", response_model=list[ExperimentTemplateResponse])
def templates(db: DbSession):
    return list_active_templates(db)