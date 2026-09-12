"""CRUD repository for users and profiles."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User, UserProfile
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def get_by_email(self, db: Session, email: str) -> User | None:
        stmt = select(User).where(User.email == email.lower())
        return db.scalars(stmt).first()

    def get_by_email_lower(self, db: Session, email: str) -> User | None:
        return self.get_by_email(db, email)

    def get_or_create_profile(self, db: Session, user_id: int) -> UserProfile:
        profile = db.scalars(select(UserProfile).where(UserProfile.user_id == user_id)).first()
        if profile is None:
            profile = UserProfile(user_id=user_id)
            db.add(profile)
            db.flush()
        return profile