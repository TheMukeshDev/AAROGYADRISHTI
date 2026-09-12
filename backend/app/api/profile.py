"""Profile endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.repositories.user import UserRepository
from app.schemas.profile import ProfileResponse, ProfileUpdate

router = APIRouter(prefix="/profile", tags=["profile"])
_repo = UserRepository()


@router.get("", response_model=ProfileResponse)
def get_profile(db: DbSession, user: CurrentUser):
    return _repo.get_or_create_profile(db, user.id)


@router.post("", response_model=ProfileResponse)
def create_profile(payload: ProfileUpdate, db: DbSession, user: CurrentUser):
    """Idempotent profile create - returns existing profile if present."""
    profile = _repo.get_or_create_profile(db, user.id)
    data = payload.model_dump(exclude_none=True)
    for key, value in data.items():
        setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile


@router.put("", response_model=ProfileResponse)
def update_profile(payload: ProfileUpdate, db: DbSession, user: CurrentUser):
    profile = _repo.get_or_create_profile(db, user.id)
    data = payload.model_dump(exclude_none=True)
    for key, value in data.items():
        setattr(profile, key, value)
    if "name" in data:
        user.name = data["name"]
    db.commit()
    db.refresh(profile)
    return profile