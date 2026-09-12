"""CRUD repositories for the Experiment Engine (Phase 3)."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.experiment import (
    Experiment,
    ExperimentDailyLog,
    ExperimentResult,
    ExperimentTemplate,
)
from app.repositories.base import BaseRepository


class ExperimentRepository(BaseRepository[Experiment]):
    def get_owned(self, db: Session, user_id: int, experiment_id: int) -> Experiment:
        exp = db.scalars(
            select(Experiment).where(Experiment.id == experiment_id, Experiment.user_id == user_id)
        ).first()
        if exp is None:
            raise NotFoundError("Experiment not found.")
        return exp

    def get_active(self, db: Session, user_id: int) -> Experiment | None:
        return db.scalars(
            select(Experiment)
            .where(Experiment.user_id == user_id, Experiment.status == "active")
            .order_by(Experiment.created_at.desc())
        ).first()

    def list_by_user(self, db: Session, user_id: int, status: str | None = None) -> list[Experiment]:
        stmt = select(Experiment).where(Experiment.user_id == user_id)
        if status is not None:
            stmt = stmt.where(Experiment.status == status)
        stmt = stmt.order_by(Experiment.created_at.desc())
        return list(db.scalars(stmt))

    def recently_completed_of_type(
        self, db: Session, user_id: int, experiment_type: str, within_days: int
    ) -> bool:
        """True if this user completed an experiment of ``type`` in the last ``within_days``."""
        from datetime import timedelta

        threshold = date.today() - timedelta(days=within_days)
        row = db.scalars(
            select(Experiment.id)
            .where(
                Experiment.user_id == user_id,
                Experiment.experiment_type == experiment_type,
                Experiment.status == "completed",
                Experiment.completed_at >= threshold,
            )
            .limit(1)
        ).first()
        return row is not None

    def create(self, db: Session, user_id: int, **fields) -> Experiment:
        exp = Experiment(user_id=user_id, **fields)
        db.add(exp)
        db.commit()
        db.refresh(exp)
        return exp


class ExperimentTemplateRepository(BaseRepository[ExperimentTemplate]):
    def get_active_by_type(self, db: Session, experiment_type: str) -> ExperimentTemplate | None:
        return db.scalars(
            select(ExperimentTemplate).where(
                ExperimentTemplate.experiment_type == experiment_type,
                ExperimentTemplate.active.is_(True),
            )
        ).first()


class ExperimentDailyLogRepository(BaseRepository[ExperimentDailyLog]):
    def get_for_date(self, db: Session, experiment_id: int, log_date: date) -> ExperimentDailyLog | None:
        return db.scalars(
            select(ExperimentDailyLog).where(
                ExperimentDailyLog.experiment_id == experiment_id,
                ExperimentDailyLog.date == log_date,
            )
        ).first()

    def upsert(
        self,
        db: Session,
        experiment_id: int,
        log_date: date,
        *,
        completed: bool | None = None,
        target_met: bool | None = None,
        notes: str | None = None,
        day_number: int | None = None,
    ) -> ExperimentDailyLog:
        row = self.get_for_date(db, experiment_id, log_date)
        if row is None:
            row = ExperimentDailyLog(
                experiment_id=experiment_id, date=log_date, completed=bool(completed),
                target_met=target_met, notes=notes, day_number=day_number,
            )
            db.add(row)
        else:
            if completed is not None:
                row.completed = completed
            if target_met is not None:
                row.target_met = target_met
            if notes is not None:
                row.notes = notes
            if day_number is not None:
                row.day_number = day_number
        db.commit()
        db.refresh(row)
        return row

    def list_for_experiment(self, db: Session, experiment_id: int) -> list[ExperimentDailyLog]:
        return list(
            db.scalars(
                select(ExperimentDailyLog)
                .where(ExperimentDailyLog.experiment_id == experiment_id)
                .order_by(ExperimentDailyLog.date)
            )
        )


class ExperimentResultRepository(BaseRepository[ExperimentResult]):
    def get_by_experiment(self, db: Session, experiment_id: int) -> ExperimentResult | None:
        return db.scalars(
            select(ExperimentResult).where(ExperimentResult.experiment_id == experiment_id)
        ).first()