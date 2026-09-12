"""Prompt building for the coach (Phase 6, section 3).

Builds the structured, aggregate-only context and the message list sent to a
provider. CRITICAL SAFETY RULE: this module never includes raw daily-log rows
or health-sync vitals - only derived summaries (pattern snapshots, experiment
evidence levels, personal-learning summaries, next-action suggestions).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.base_provider import CoachContext
from app.ai.safety_guard import is_prohibited_user_question
from app.models.evaluation import LearningCandidate
from app.models.experiment import Experiment, ExperimentResult
from app.models.personal_learning import PersonalLearning
from app.models.user import UserProfile
from app.repositories.daily_log import DailyLogRepository
from app.services.experiment_templates import meta_for

_MAX_PATTERNS = 3
_MAX_LEARNINGS = 2


def build_context(db: Session, user, next_action: dict | None = None) -> CoachContext:
    """Assemble the aggregate context the coach is allowed to see."""
    from app.analytics.config import AnalyticsConfig
    from app.analytics.engine import AnalyticsEngine

    profile = db.get(UserProfile, user.id)

    bundle = AnalyticsEngine(AnalyticsConfig()).run(db, user.id)
    pattern_snapshots = [
        {
            "pattern_id": p.pattern_type,
            "feature_label": p.feature_label,
            "target_label": p.target_label,
            "strength": p.strength,
            "strength_label": p.strength_label,
            "correlation": p.correlation if isinstance(p.correlation, (int, float)) else None,
        }
        for p in bundle.patterns
        if p.has_pattern
    ][:_MAX_PATTERNS]

    active = db.scalars(
        select(Experiment)
        .where(Experiment.user_id == user.id, Experiment.status == "active")
        .order_by(Experiment.created_at.desc())
    ).first()

    recent = list(
        db.scalars(
            select(Experiment)
            .where(Experiment.user_id == user.id, Experiment.status == "completed")
            .order_by(Experiment.completed_at.desc())
            .limit(2)
        )
    )
    recent_experiments = []
    for exp in recent:
        result = db.scalars(
            select(ExperimentResult).where(ExperimentResult.experiment_id == exp.id)
        ).first()
        recent_experiments.append(
            {
                "experiment_type": exp.experiment_type,
                "title": exp.title,
                "intervention": exp.intervention,
                "duration_days": exp.duration_days,
                "evidence_level": (result.confidence_level if result else "INSUFFICIENT"),
            }
        )

    learnings = list(
        db.scalars(
            select(PersonalLearning)
            .where(
                PersonalLearning.user_id == user.id,
                PersonalLearning.state != "dismissed",
                PersonalLearning.evidence_level != "INSUFFICIENT",
            )
            .order_by(PersonalLearning.updated_at.desc())
            .limit(_MAX_LEARNINGS)
        )
    )

    days = DailyLogRepository().distinct_dates(db, user.id)

    return CoachContext(
        user_name=profile.full_name if profile else None,
        patterns=pattern_snapshots,
        active_experiment=(
            {
                "title": active.title,
                "intervention": active.intervention,
                "duration_days": active.duration_days,
                "days_left": max((active.end_date - active.start_date).days + 1, 1),
            }
            if active
            else None
        ),
        recent_experiments=recent_experiments,
        learnings=[
            {"pattern_type": l.pattern_type, "intervention": l.intervention, "summary": l.summary or ""}
            for l in learnings
        ],
        next_action=next_action,
        has_daily_data=days > 0,
        days_tracked=days,
    )


_SYSTEM_PROMPT = (
    "You are AarogyaDrishti\u2019s preventive lifestyle coach. You ONLY have access to the "
    "structured context provided - personal pattern snapshots, experiment evidence levels, "
    "personal learning summaries and suggested next actions. You NEVER see raw daily logs or "
    "health device readings. You talk about habits and lifestyle only: you do not diagnose, "
    "predict disease, or give medical / medication / dosage advice. If a question needs a "
    "clinician, say so and suggest talking to one. Keep replies short, encouraging and grounded "
    "in the provided context. Never claim causation."
)


def build_messages(user_text: str, context: CoachContext, history: list[dict] | None = None) -> list[dict]:
    """Build the message list for remote providers."""
    messages: list[dict] = [{"role": "system", "content": _SYSTEM_PROMPT}]
    if history:
        messages.extend(history[-6:])
    if is_prohibited_user_question(user_text):
        user_text = (
            user_text
            + "\n\n[Note: the user is asking something outside this coach's scope - remind "
            "them gently that you only work with lifestyle observations and that medical "
            "questions should go to a clinician.]"
        )
    messages.append(
        {
            "role": "user",
            "content": f"Context: {context.to_dict()}\n\nUser message: {user_text}",
        }
    )
    return messages