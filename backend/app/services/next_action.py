"""Deterministic next-action service (Phase 6).

Picks the single most useful next step for the user from a fixed rule set -
never medical, always grounded in the user's own current state:
``collect_more_data``, ``continue_routine``, ``start_experiment``,
``repeat_experiment``, ``review_pattern``, ``rest_and_observe``.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.experiment import Experiment
from app.models.personal_learning import PersonalLearning
from app.repositories.daily_log import DailyLogRepository


def determine_next_action(db: Session, user) -> dict:
    status = _snapshot(db, user.id)
    days = status["days_tracked"]

    if status["active"]:
        exp = status["active"]
        return {
            "action_type": "continue_routine",
            "heading": "Keep the current experiment going",
            "reason": f"Stick with \"{exp.intervention}\" for the remaining days - the observation is only as good as its completion.",
        }

    if days == 0:
        return {
            "action_type": "collect_more_data",
            "heading": "Start with a few daily check-ins",
            "reason": "A recommendation need a little data first - a 7-day baseline of your habits makes everything else meaningful.",
        }

    if status["recommendation"]:
        rec = status["recommendation"]
        return {
            "action_type": "start_experiment",
            "heading": "Try a structured experiment",
            "reason": f"The pattern in your data (\"{rec['pattern_type']}\") is worth testing with the {rec['experiment_type']} experiment.",
        }

    if status["recently_completed"]:
        return {
            "action_type": "review_pattern",
            "heading": "Look at your latest result",
            "reason": "Your last experiment produced evidence - reviewing it and accepting or rejecting the observation keeps your profile honest.",
        }

    if status["learning_count"] > 0 and status["possible_repeat"]:
        return {
            "action_type": "repeat_experiment",
            "heading": "Confirm an observation with a repeat",
            "reason": "A repeated experiment is how early observations become more reliable - same experiment, fresh week.",
        }

    return {
        "action_type": "rest_and_observe",
        "heading": "Keep observing",
        "reason": "Nothing needs changing right now. Keep logging your check-ins and I'll keep watching the patterns.",
    }


def _snapshot(db: Session, user_id: int) -> dict:
    days = DailyLogRepository().distinct_dates(db, user_id)
    active = db.scalars(
        select(Experiment).where(Experiment.user_id == user_id, Experiment.status == "active")
    ).first()

    recently_completed = db.scalars(
        select(Experiment).where(
            Experiment.user_id == user_id, Experiment.status == "completed"
        ).order_by(Experiment.completed_at.desc())
    ).first()

    completed_count = len(
        list(
            db.scalars(
                select(Experiment).where(
                    Experiment.user_id == user_id, Experiment.status == "completed"
                )
            )
        )
    )

    learnings = list(
        db.scalars(
            select(PersonalLearning).where(
                PersonalLearning.user_id == user_id,
                PersonalLearning.state != "dismissed",
                PersonalLearning.evidence_level != "INSUFFICIENT",
            )
        )
    )

    recommendation = None
    if days >= 7 and active is None:
        from app.services.experiment_recommendation import recommend
        from app.models.user import User

        user_obj = db.get(User, user_id)
        if user_obj is None:  # pragma: no cover - defensive for callers without a User
            user_obj = User(id=user_id)
        try:
            resp = recommend(db, user_obj)
        except Exception:  # pragma: no cover - recommendation is best-effort
            resp = None
        if resp is not None and resp.recommendation is not None:
            recommendation = {
                "experiment_type": resp.recommendation.experiment_type,
                "pattern_type": resp.recommendation.pattern.pattern_id,
            }

    return {
        "days_tracked": days,
        "active": active,
        "recently_completed": recently_completed,
        "completed_count": completed_count,
        "learning_count": len(learnings),
        "possible_repeat": completed_count > 0,
        "recommendation": recommendation,
    }