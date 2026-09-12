"""CRUD repository for consent records."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.consent import ConsentRecord
from app.repositories.base import BaseRepository


class ConsentRepository(BaseRepository[ConsentRecord]):
    def latest_for(self, db: Session, user_id: int, data_type: str) -> ConsentRecord | None:
        return db.scalars(
            select(ConsentRecord)
            .where(ConsentRecord.user_id == user_id, ConsentRecord.data_type == data_type)
            .order_by(ConsentRecord.timestamp.desc())
            .limit(1)
        ).first()

    def record(self, db: Session, user_id: int, data_type: str, consent_given: bool, revoked: bool = False) -> ConsentRecord:
        row = ConsentRecord(
            user_id=user_id,
            data_type=data_type,
            consent_given=consent_given,
            revoked=revoked,
            timestamp=datetime.now(timezone.utc),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    def status(self, db: Session, user_id: int) -> dict[str, bool]:
        types = ("steps", "sleep", "activity", "screen_time", "demographic_optional")
        status: dict[str, bool] = {}
        for t in types:
            latest = self.latest_for(db, user_id, t)
            status[t] = bool(latest and latest.consent_given and not latest.revoked)
        return status