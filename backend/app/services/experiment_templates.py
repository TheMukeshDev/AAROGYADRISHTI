"""Predefined experiment templates (Phase 3, section 2) + seeding.

Templates are conservative, wellness-oriented interventions. They are NEVER
medical treatments, medication recommendations, diagnoses or claims.

The DB rows hold the user-facing copy; ``TEMPLATE_META`` holds the code-side
logic (which pattern triggers the experiment, which metric the before/after
comparison keys on, and which metrics participate in numeric comparisons).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.experiment import ExperimentTemplate

TEMPLATES: list[dict] = [
    {
        "experiment_type": "sleep_consistency",
        "title": "7-Day Sleep Consistency Experiment",
        "description": (
            "Test what happens when you keep a consistent 7+ hours of sleep "
            "for one week."
        ),
        "hypothesis_template": (
            "Maintaining a more consistent sleep duration may be associated "
            "with improved next-day energy."
        ),
        "intervention": "Aim for at least 7 hours of sleep for 7 days.",
        "duration_days": 7,
        "required_metrics": ["sleep_hours", "sleep_quality", "energy", "stress", "mood"],
        "active": True,
    },
    {
        "experiment_type": "night_screen_reduction",
        "title": "7-Day Night Screen Reduction Experiment",
        "description": (
            "Test what happens when you stop recreational screen use 30 minutes "
            "before bedtime for one week."
        ),
        "hypothesis_template": (
            "Reducing late-night screen use may be associated with longer, "
            "more consistent sleep."
        ),
        "intervention": "Avoid recreational screen use for 30 minutes before bedtime for 7 days.",
        "duration_days": 7,
        "required_metrics": ["sleep_hours", "sleep_quality", "screen_time_minutes", "energy"],
        "active": True,
    },
    {
        "experiment_type": "daily_activity",
        "title": "7-Day Daily Activity Experiment",
        "description": (
            "Test what happens when you hit a reasonable daily walking/activity "
            "target for one week."
        ),
        "hypothesis_template": (
            "A consistent daily activity target may be associated with an "
            "improved mood."
        ),
        "intervention": "Complete a reasonable daily walking/activity target for 7 days.",
        "duration_days": 7,
        "required_metrics": ["steps", "active_minutes", "mood", "energy", "stress"],
        "active": True,
    },
]

# Which Phase 2 pattern_type triggers each experiment + analysis logic.
TEMPLATE_META: dict[str, dict] = {
    "sleep_consistency": {
        "pattern_type": "sleep_energy",
        "primary_metric": "energy",
        "higher_is_better": True,
        "track_metrics": ["sleep_hours", "energy", "stress", "mood"],
    },
    "night_screen_reduction": {
        "pattern_type": "screen_sleep",
        "primary_metric": "sleep_hours",
        "higher_is_better": True,
        "track_metrics": ["screen_time_minutes", "sleep_hours", "energy"],
    },
    "daily_activity": {
        "pattern_type": "activity_mood",
        "primary_metric": "mood",
        "higher_is_better": True,
        "track_metrics": ["steps", "active_minutes", "mood", "energy", "stress"],
    },
}

# Map experiment_type back to a Phase 2 pattern_type for the learning block.
def learning_type_for(experiment_type: str) -> str:
    meta = TEMPLATE_META.get(experiment_type, {})
    return meta.get("pattern_type", experiment_type)


def seed_experiment_templates(db: Session) -> int:
    """Upsert the predefined templates. Idempotent; returns row count."""
    seeded = 0
    for values in TEMPLATES:
        experiment_type = values["experiment_type"]
        existing = db.scalars(
            select(ExperimentTemplate).where(ExperimentTemplate.experiment_type == experiment_type)
        ).first()
        if existing is None:
            db.add(ExperimentTemplate(**values))
            seeded += 1
        elif not existing.active:
            existing.active = True
            seeded += 1
    db.commit()
    return seeded


def get_template(db: Session, experiment_type: str) -> ExperimentTemplate:
    template = db.scalars(
        select(ExperimentTemplate).where(
            ExperimentTemplate.experiment_type == experiment_type,
            ExperimentTemplate.active.is_(True),
        )
    ).first()
    if template is None:
        raise NotFoundError("No experiment template found for this experiment type.")
    return template


def list_active_templates(db: Session) -> list[ExperimentTemplate]:
    return list(
        db.scalars(
            select(ExperimentTemplate).where(ExperimentTemplate.active.is_(True)).order_by(ExperimentTemplate.id)
        )
    )


def meta_for(experiment_type: str) -> dict:
    return TEMPLATE_META.get(experiment_type, {"primary_metric": "energy", "higher_is_better": True, "track_metrics": []})