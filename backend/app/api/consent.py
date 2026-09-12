"""Consent endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.repositories.consent import ConsentRepository
from app.schemas.consent import ConsentRecordIn, ConsentRecordOut, ConsentStatus

router = APIRouter(prefix="/consent", tags=["consent"])
_repo = ConsentRepository()


@router.post("", response_model=ConsentRecordOut, status_code=201)
def record_consent(payload: ConsentRecordIn, db: DbSession, user: CurrentUser):
    return _repo.record(db, user.id, payload.data_type, payload.consent_given)


@router.get("", response_model=ConsentStatus)
def get_consent(db: DbSession, user: CurrentUser):
    return ConsentStatus(**_repo.status(db, user.id))