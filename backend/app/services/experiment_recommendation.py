"""Experiment recommendation engine (Phase 3, section 10; refined by Phase 5).

The recommendation is computed from REAL Phase 2 patterns produced by the
analytics engine - there is no hardcoded recommendation. A recommendation is
only returned when:

- a pattern actually exists for the user (confidence moderate/high),
- the pattern maps to a safe, predefined experiment template,
- the user has no conflicting active experiment,
- the same experiment was not completed very recently.

Phase 5 augments each recommendation with what the personal learning profile
already says about that relationship.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.analytics.config import AnalyticsConfig
from app.analytics.engine import AnalyticsEngine
from app.analytics.patterns import PatternResult
from app.core.config import get_settings
from app.models.experiment import Experiment, ExperimentTemplate
from app.models.user import User
from app.schemas.experiment import (
    ExperimentRecommendation,
    LearningContext,
    PatternSnapshot,
    RecommendationResponse,
)
from app.services.experiment_templates import (
    TEMPLATE_META,
    seed_experiment_templates,
)

_STRENGTH_RANK = {"none": 3, "early": 1, "emerging": 0}

_WHY_TEMPLATES: dict[tuple[str, str], str] = {
    ("sleep_energy", "positive"): "Your data shows that your next-day energy has tended to be higher after longer sleep.",
    ("sleep_energy", "negative"): "Your data shows that your next-day energy has tended to be lower after longer sleep.",
    ("screen_sleep", "negative"): "Your data shows that your sleep has tended to be shorter on days after late-night screen use.",
    ("screen_sleep", "positive"): "Your data shows that your sleep has tended to be longer after late-night screen use.",
    ("activity_mood", "positive"): "Your data shows that your mood has tended to be better on days with more activity.",
    ("activity_mood", "negative"): "Your data shows that your mood has tended to be lower on days with more activity.",
    ("exercise_stress", "negative"): "Your data shows that your stress has tended to be lower on exercise days.",
    ("hydration_energy", "positive"): "Your data shows that your energy has tended to be higher on days you drank more water.",
    ("food_energy", "positive"): "Your data shows that your energy has tended to be higher on days with healthier meals.",
    ("caffeine_sleep", "negative"): "Your data shows that your sleep has tended to be shorter on days you had caffeine.",
}
_WHY_FALLBACK = "Your data shows an association worth testing with a structured experiment."


@dataclass
class _Candidate:
    pattern: PatternResult
    experiment_type: str
    rank: tuple[int, float, float]  # (strength_rank, -confidence_score, -|corr|)


def _build_why(pattern: PatternResult) -> str:
    text = _WHY_TEMPLATES.get((pattern.pattern_type, pattern.direction), _WHY_FALLBACK)
    if pattern.n < 14:
        return f"Your earlier check-ins suggest an association. {text}"
    return text


def _candidates(patterns: list[PatternResult]) -> list[_Candidate]:
    result: list[_Candidate] = []
    for pattern in patterns:
        if not pattern.has_pattern:
            continue
        if pattern.confidence.level not in ("moderate", "high"):
            continue
        experiment_type = _experiment_type_for(pattern.pattern_type)
        if experiment_type is None:
            continue
        rank = (
            _STRENGTH_RANK.get(pattern.strength, 1),
            -pattern.confidence.score,
            -abs(pattern.correlation or 0.0),
        )
        result.append(_Candidate(pattern=pattern, experiment_type=experiment_type, rank=rank))
    result.sort(key=lambda c: c.rank)
    return result


def _experiment_type_for(pattern_type: str) -> str | None:
    for experiment_type, meta in TEMPLATE_META.items():
        if meta.get("pattern_type") == pattern_type:
            return experiment_type
    return None


def _learning_context_for(db: Session, user: User, pattern_type: str) -> LearningContext:
    try:
        from app.services.personal_learning import PersonalLearningService

        return PersonalLearningService().context_for_pattern(db, user.id, pattern_type)
    except ImportError:
        return LearningContext()


def recommend(db: Session, user: User) -> RecommendationResponse:
    seed_experiment_templates(db)
    settings = get_settings()

    active = db.scalars(
        select(Experiment).where(
            Experiment.user_id == user.id, Experiment.status == "active"
        ).order_by(Experiment.created_at.desc())
    ).first()
    if active is not None:
        return RecommendationResponse(
            recommendation=None,
            has_active_experiment=True,
            active_experiment_id=active.id,
            reason="You already have an active experiment - finish it before starting another.",
        )

    bundle = AnalyticsEngine(AnalyticsConfig()).run(db, user.id)
    for candidate in _candidates(bundle.patterns):
        if _recently_completed(db, user.id, candidate.experiment_type, settings.experiment_cooldown_days):
            continue

        template = db.scalars(
            select(ExperimentTemplate).where(
                ExperimentTemplate.experiment_type == candidate.experiment_type,
                ExperimentTemplate.active.is_(True),
            )
        ).first()
        if template is None:
            continue

        pattern = candidate.pattern
        why = _build_why(pattern)
        snapshot = PatternSnapshot(
            pattern_id=pattern.pattern_type,
            feature_label=pattern.feature_label,
            target_label=pattern.target_label,
            direction=pattern.direction,
            correlation=pattern.correlation,
            sample_size=pattern.n,
            strength=pattern.strength,
            strength_label=pattern.strength_label,
            why=why,
        )
        return RecommendationResponse(
            recommendation=ExperimentRecommendation(
                experiment_type=template.experiment_type,
                title=template.title,
                why=why,
                pattern=snapshot,
                hypothesis=template.hypothesis_template,
                intervention=template.intervention,
                duration_days=template.duration_days,
                metrics=list(template.required_metrics or []),
                learning_context=_learning_context_for(db, user, pattern.pattern_type),
            ),
            has_active_experiment=False,
            reason="Based on your observed personally detected patterns.",
        )

    return RecommendationResponse(
        recommendation=None,
        has_active_experiment=False,
        reason="We don't have a strong enough personal pattern to recommend an experiment yet.",
    )


def _recently_completed(db: Session, user_id: int, experiment_type: str, within_days: int) -> bool:
    threshold = datetime.utcnow() - timedelta(days=within_days)
    count = db.scalars(
        select(func.count(Experiment.id)).where(
            Experiment.user_id == user_id,
            Experiment.experiment_type == experiment_type,
            Experiment.status == "completed",
            Experiment.completed_at >= threshold,
        )
    ).one()
    return int(count) > 0