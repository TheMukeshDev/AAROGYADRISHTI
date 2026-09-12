"""CRUD repository for daily lifestyle logs."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.errors import ConflictError, NotFoundError
from app.models.daily_log import DailyLog
from app.repositories.base import BaseRepository


class DailyLogRepository(BaseRepository[DailyLog]):
    def get_for_user_date(self, db: Session, user_id: int, log_date: date) -> DailyLog | None:
        return db.scalars(
            select(DailyLog).where(DailyLog.user_id == user_id, DailyLog.date == log_date)
        ).first()

    def create(self, db: Session, user_id: int, **fields) -> DailyLog:
        existing = self.get_for_user_date(db, user_id, fields["date"])
        if existing is not None:
            raise ConflictError("You already submitted a check-in for this date.")
        log = DailyLog(user_id=user_id, **fields)
        db.add(log)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise ConflictError("You already submitted a check-in for this date.") from exc
        db.refresh(log)
        return log

    def update(self, db: Session, user_id: int, log_date: date, **fields) -> DailyLog:
        log = self.get_for_user_date(db, user_id, log_date)
        if log is None:
            raise NotFoundError("No check-in found for this date.")
        for key, value in fields.items():
            setattr(log, key, value)
        db.commit()
        db.refresh(log)
        return log

    def list_recent(self, db: Session, user_id: int, limit: int = 90) -> list[DailyLog]:
        stmt = (
            select(DailyLog)
            .where(DailyLog.user_id == user_id)
            .order_by(DailyLog.date.desc())
            .limit(limit)
        )
        return list(db.scalars(stmt))

    def list_in_range(
        self, db: Session, user_id: int, start: date | None = None, end: date | None = None
    ) -> list[DailyLog]:
        stmt = select(DailyLog).where(DailyLog.user_id == user_id)
        if start is not None:
            stmt = stmt.where(DailyLog.date >= start)
        if end is not None:
            stmt = stmt.where(DailyLog.date <= end)
        return list(db.scalars(stmt.order_by(DailyLog.date)))

    def distinct_dates(self, db: Session, user_id: int) -> int:
        stmt = select(DailyLog.date).where(DailyLog.user_id == user_id).distinct()
        return len(list(db.scalars(stmt)))