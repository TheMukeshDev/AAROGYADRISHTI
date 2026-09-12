"""CRUD repositories for the personal learning profile (Phase 5)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.personal_learning import PersonalLearning, PersonalLearningEvidence
from app.repositories.base import BaseRepository


class PersonalLearningRepository(BaseRepository[PersonalLearning]):
    def get_owned(self, db: Session, user_id: int, learning_id: int) -> PersonalLearning:
        row = db.scalars(
            select(PersonalLearning).where(
                PersonalLearning.id == learning_id, PersonalLearning.user_id == user_id
            )
        ).first()
        if row is None:
            raise NotFoundError("Personal learning not found.")
        return row

    def by_key(self, db: Session, user_id: int, pattern_type: str, intervention: str) -> PersonalLearning | None:
        return db.scalars(
            select(PersonalLearning).where(
                PersonalLearning.user_id == user_id,
                PersonalLearning.pattern_type == pattern_type,
                PersonalLearning.intervention == intervention,
            )
        ).first()

    def list_for_user(self, db: Session, user_id: int, include_dismissed: bool = False) -> list[PersonalLearning]:
        stmt = select(PersonalLearning).where(PersonalLearning.user_id == user_id)
        if not include_dismissed:
            stmt = stmt.where(PersonalLearning.state != "dismissed")
        return list(db.scalars(stmt.order_by(PersonalLearning.evidence_level.desc(), PersonalLearning.updated_at.desc())))

    def list_observable(self, db: Session, user_id: int) -> list[PersonalLearning]:
        return list(
            db.scalars(
                select(PersonalLearning).where(
                    PersonalLearning.user_id == user_id,
                    PersonalLearning.state != "dismissed",
                    PersonalLearning.evidence_level != "INSUFFICIENT",
                )
            )
        )


class PersonalLearningEvidenceRepository(BaseRepository[PersonalLearningEvidence]):
    def list_for_learning(self, db: Session, learning_id: int) -> list[PersonalLearningEvidence]:
        return list(
            db.scalars(
                select(PersonalLearningEvidence)
                .where(PersonalLearningEvidence.learning_id == learning_id)
                .order_by(PersonalLearningEvidence.id)
            )
        )

    def delete_for_learning(self, db: Session, learning_id: int) -> None:
        for row in db.scalars(
            select(PersonalLearningEvidence).where(PersonalLearningEvidence.learning_id == learning_id)
        ):
            db.delete(row)
        db.flush()