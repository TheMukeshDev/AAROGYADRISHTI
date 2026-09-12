"""Base repository - thin generic CRUD over a SQLAlchemy session."""

from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.base import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """Shared ordering helpers for repositories.

    Kept minimal on purpose - Phase 1 does not need a full generic CRUD
    framework, but centralising session plumbing keeps modules easy to test.
    """

    def get(self, db: Session, model_type: type[T], object_id: int) -> T | None:
        return db.get(model_type, object_id)

    def list_by_user(self, db: Session, model_type: type[T], user_id: int) -> list[T]:
        return list(db.scalars(select(model_type).where(model_type.user_id == user_id)))

    def count_by_user(self, db: Session, model_type: type[T], user_id: int) -> int:
        return len(self.list_by_user(db, model_type, user_id))