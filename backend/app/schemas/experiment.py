"""Experiment Engine request/response schemas (Phase 3 + Phase 4 evaluation).

Wire shapes only. All numeric/statistical structures are produced by the
deterministic analytics modules; these classes only move JSON over the wire.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import Message


# --- Templates ---------------------------------------------------------------
class ExperimentTemplateResponse(BaseModel):
    id: int
    experiment_type: str
    title: str
    description: str
    hypothesis_template: str
    intervention: str
    duration_days: int
    required_metrics: list[str]
    active: bool = True

    model_config = ConfigDict(from_attributes=True)


# --- Recommendation -----------------------------------------------------------
class PatternSnapshot(BaseModel):
    pattern_id: str
    feature_label: str
    target_label: str
    direction: str | None = None
    correlation: float | None = None
    sample_size: int = 0
    strength: str = "none"
    strength_label: str = "Not enough data"
    why: str = ""


class LearningContext(BaseModel):
    has_learning: bool = False
    evidence_level: str | None = None
    evidence_state: str | None = None
    note: str | None = None


class ExperimentRecommendation(BaseModel):
    experiment_type: str
    title: str
    why: str
    pattern: PatternSnapshot
    hypothesis: str
    intervention: str
    duration_days: int
    metrics: list[str]
    learning_context: LearningContext = Field(default_factory=LearningContext)


class RecommendationResponse(BaseModel):
    recommendation: ExperimentRecommendation | None = None
    has_active_experiment: bool = False
    active_experiment_id: int | None = None
    reason: str | None = None


# --- Experiments --------------------------------------------------------------
class ExperimentStartRequest(BaseModel):
    experiment_type: str


class ExperimentResponse(BaseModel):
    id: int
    pattern_id: str | None = None
    experiment_type: str
    title: str
    hypothesis: str
    intervention: str
    duration_days: int
    start_date: dt.date
    end_date: dt.date
    status: str
    completed_at: dt.datetime | None = None
    created_at: dt.datetime

    model_config = ConfigDict(from_attributes=True)


class ExperimentDailyLogRequest(BaseModel):
    date: dt.date | None = None
    completed: bool = True
    target_met: bool | None = None
    notes: str | None = Field(default=None, max_length=1000)
    # Optional metric values for this date - they are written into the user's
    # existing daily-log row (Phase 3 reuses the Phase 1 system).
    metrics: dict[str, Any] | None = None


class ExperimentDailyLogResponse(BaseModel):
    id: int
    experiment_id: int
    date: dt.date
    completed: bool
    target_met: bool | None = None
    notes: str | None = None
    day_number: int | None = None

    model_config = ConfigDict(from_attributes=True)


class ActiveExperimentResponse(BaseModel):
    experiment: ExperimentResponse | None = None


# --- Evaluation (Phase 4, surfaced through Phase 3 result screens) -----------
class MetricComparisonResponse(BaseModel):
    metric: str
    baseline_mean: float | None = None
    experiment_mean: float | None = None
    baseline_median: float | None = None
    experiment_median: float | None = None
    difference: float | None = None
    percentage_change: float | None = None
    sample_size: int = 0
    valid_observations: int = 0
    direction: str = "no_change"  # improved | worsened | no_change


class ExperimentResultResponse(BaseModel):
    experiment_id: int
    status: str = "completed"
    metrics: list[MetricComparisonResponse] = []
    data_completeness: float = 0.0
    sample_size: int = 0
    target_adherence: float | None = None
    target_adherence_text: str | None = None
    consistency_score: float | None = None
    evidence_level: str = "INSUFFICIENT"
    causality_proven: bool = False
    summary: str = ""
    limitations: str = ""
    learning: dict[str, Any] = {}


class ExperimentHistoryItem(BaseModel):
    experiment: ExperimentResponse
    result: ExperimentResultResponse | None = None


class ExperimentDetailResponse(BaseModel):
    experiment: ExperimentResponse
    daily_logs: list[ExperimentDailyLogResponse] = []
    target: str | None = None
    today: dt.date
    days_into: int = 0  # 1-based day the user is on (for active experiments)
    progress_percent: int = 0


# --- Learning candidates (Phase 4) -------------------------------------------
class LearningCandidateResponse(BaseModel):
    id: int
    user_id: int
    experiment_id: int
    pattern_type: str
    intervention: str
    observed_change: dict[str, Any]
    evidence_level: str
    status: str = "candidate"
    causality_proven: bool = False
    created_at: dt.datetime

    model_config = ConfigDict(from_attributes=True)


class LearningCandidateListResponse(BaseModel):
    candidates: list[LearningCandidateResponse]


class ExperimentEvidenceResponse(BaseModel):
    id: int
    experiment_id: int
    data_completeness: float
    target_adherence: float | None = None
    consistency_score: float | None = None
    evidence_level: str
    reason: str
    limitations: str
    causality_proven: bool = False

    model_config = ConfigDict(from_attributes=True)


class AcceptRejectResponse(Message):
    status: str