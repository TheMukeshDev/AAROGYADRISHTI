"""CRUD repository for health connections and synced health data."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.health import DailyHealthData, HealthConnection
from app.repositories.base import BaseRepository


class HealthRepository(BaseRepository[HealthConnection]):
    def get_connection(self, db: Session, user_id: int, provider: str) -> HealthConnection | None:
        return db.scalars(
            select(HealthConnection).where(
                HealthConnection.user_id == user_id, HealthConnection.provider == provider
            )
        ).first()

    def upsert_connection(self, db: Session, user_id: int, **fields) -> HealthConnection:
        conn = self.get_connection(db, user_id, fields["provider"])
        if conn is None:
            conn = HealthConnection(user_id=user_id, **fields)
            db.add(conn)
        else:
            for key, value in fields.items():
                setattr(conn, key, value)
        db.commit()
        db.refresh(conn)
        return conn


class DailyHealthDataRepository(BaseRepository[DailyHealthData]):
    def get_for_user_date_source(self, db: Session, user_id: int, d: date, source: str) -> DailyHealthData | None:
        return db.scalars(
            select(DailyHealthData).where(
                DailyHealthData.user_id == user_id,
                DailyHealthData.date == d,
                DailyHealthData.source == source,
            )
        ).first()

    def upsert(self, db: Session, user_id: int, d: date, source: str, synced_at: datetime, **values) -> DailyHealthData:
        row = self.get_for_user_date_source(db, user_id, d, source)
        if row is None:
            row = DailyHealthData(user_id=user_id, date=d, source=source, synced_at=synced_at, **values)
            db.add(row)
        else:
            for key, value in values.items():
                setattr(row, key, value)
            row.synced_at = synced_at
        db.commit()
        db.refresh(row)
        return row