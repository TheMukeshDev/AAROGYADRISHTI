"""Personal learning profile endpoints (Phase 5, section 15).

Ownership is enforced via the repository - users can only ever read, dismiss
or reopen their own learnings. Recalculation is idempotent and deterministic.
"""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.models.personal_learning import PersonalLearning
from app.repositories.personal_learning import PersonalLearningEvidenceRepository
from app.schemas.learning import (
    DismissReopenResponse,
    PersonalLearningDetailResponse,
    PersonalLearningEvidenceResponse,
    PersonalLearningListResponse,
    PersonalLearningRecalcResponse,
    PersonalLearningResponse,
    PersonalLearningSummaryResponse,
)
from app.services.personal_learning import PersonalLearningService

router = APIRouter(tags=["learning"])
_service = PersonalLearningService()
_evidence_repo = PersonalLearningEvidenceRepository()


@router.get("/learnings/personal/summary", response_model=PersonalLearningSummaryResponse)
def learning_summary(db: DbSession, user: CurrentUser):
    rows = list(
        db.scalars(select(PersonalLearning).where(PersonalLearning.user_id == user.id))
    )
    counts = {"proposed": 0, "confirmed": 0, "dismissed": 0}
    for row in rows:
        counts[row.state] = counts.get(row.state, 0) + 1
    visible = [row for row in rows if row.state != "dismissed" and row.evidence_level != "INSUFFICIENT"]
    top = visible[0] if visible else None
    return PersonalLearningSummaryResponse(
        total=len(rows),
        proposed=counts.get("proposed", 0),
        confirmed=counts.get("confirmed", 0),
        dismissed=counts.get("dismissed", 0),
        top_learning=PersonalLearningResponse.model_validate(top) if top else None,
    )


@router.post("/learnings/personal", response_model=PersonalLearningRecalcResponse)
def recalculate_learnings(db: DbSession, user: CurrentUser):
    learnings = _service.recalculate_all(db, user.id)
    return PersonalLearningRecalcResponse(
        recomputed=True,
        count=len(learnings),
        learnings=[PersonalLearningResponse.model_validate(row) for row in learnings],
    )


@router.get("/learnings/personal", response_model=PersonalLearningListResponse)
def list_learnings(db: DbSession, user: CurrentUser, include_dismissed: bool = False):
    rows = _service.learnings.list_for_user(db, user.id, include_dismissed=include_dismissed)
    return PersonalLearningListResponse(
        learnings=[PersonalLearningResponse.model_validate(row) for row in rows],
        count=len(rows),
    )


@router.get("/learnings/personal/{learning_id}", response_model=PersonalLearningDetailResponse)
def learning_detail(learning_id: int, db: DbSession, user: CurrentUser):
    row = _service.learnings.get_owned(db, user.id, learning_id)
    evidence = _evidence_repo.list_for_learning(db, row.id)
    return PersonalLearningDetailResponse(
        **PersonalLearningResponse.model_validate(row).model_dump(),
        evidence=[PersonalLearningEvidenceResponse.model_validate(e) for e in evidence],
    )


@router.delete("/learnings/personal/{learning_id}", response_model=DismissReopenResponse)
def dismiss_learning(learning_id: int, db: DbSession, user: CurrentUser):
    row = _service.learnings.get_owned(db, user.id, learning_id)
    row.state = "dismissed"
    db.commit()
    return DismissReopenResponse(state="dismissed", message="Learning dismissed. I will keep the underlying data but it will no longer appear in your profile.")


@router.patch("/learnings/personal/{learning_id}", response_model=DismissReopenResponse)
def reopen_learning(learning_id: int, db: DbSession, user: CurrentUser):
    row = _service.learnings.get_owned(db, user.id, learning_id)
    row.state = "proposed" if row.sample_size else "proposed"
    db.commit()
    return DismissReopenResponse(state=row.state, message="Learning restored to your profile.")