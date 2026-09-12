"""Personal learning profile schemas (Phase 5)."""

from __future__ import annotations

import datetime as dt
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.schemas.common import Message


class PersonalLearningEvidenceResponse(BaseModel):
    id: int
    experiment_id: int | None = None
    source: str = "candidate"
    evidence_level: str
    direction: str = "no_change"
    effect_magnitude: float | None = None
    observed_change: dict[str, Any] | None = None
    created_at: dt.datetime

    model_config = ConfigDict(from_attributes=True)


class PersonalLearningResponse(BaseModel):
    id: int
    user_id: int
    pattern_type: str
    intervention: str
    target_metric: str | None = None
    state: str = "proposed"
    evidence_level: str = "INSUFFICIENT"
    evidence_state: str = "insufficient"
    consistency_score: float | None = None
    sample_size: int = 0
    hypothesis: str | None = None
    summary: str | None = None
    causality_proven: bool = False
    created_at: dt.datetime
    updated_at: dt.datetime

    model_config = ConfigDict(from_attributes=True)


class PersonalLearningDetailResponse(PersonalLearningResponse):
    evidence: list[PersonalLearningEvidenceResponse] = []


class PersonalLearningListResponse(BaseModel):
    learnings: list[PersonalLearningResponse]
    count: int


class PersonalLearningSummaryResponse(BaseModel):
    total: int
    proposed: int
    confirmed: int
    dismissed: int
    top_learning: PersonalLearningResponse | None = None


class PersonalLearningRecalcResponse(BaseModel):
    recomputed: bool
    count: int
    learnings: list[PersonalLearningResponse]


class DismissReopenResponse(Message):
    state: str