"""Explainability layer (Phase 2, section 12).

Every surfaced pattern must answer:

1. What did we observe?
2. What data supports it?
3. How strong is the pattern?
4. What does it NOT mean?

The language here is the cautious-language boundary (section 15): observations,
associations and tendencies only. Never causation, risk, diagnosis or disease.
"""

from __future__ import annotations

from app.analytics.patterns import PatternResult

DISCLAIMER = (
    "This is a personal observation from your logged data, not a medical "
    "diagnosis or proof of causation."
)

LIMITATION_NOT_ENOUGH_DATA = (
    "This is based on fewer than 14 logged days. More check-ins will make the "
    "pattern more reliable."
)

LIMITATION_SMALL_SAMPLE = "Small personal sample - the association is consistent but can change as you log more days."


def _fmt(value: float, target_label: str) -> str:
    if target_label in ("energy", "stress", "mood"):
        return f"{value:.1f}/10" if target_label == "energy" else f"{value:.1f}"
    if target_label in ("sleep hours",):
        return f"{value:.1f} hours"
    return f"{value:.1f}"


def build_evidence(result: PatternResult) -> str:
    """Supporting-data sentence: mean target in the low vs high bucket."""
    if result.mean_low is None or result.mean_high is None:
        return "Supporting data is still being collected for this pattern."
    return (
        f"{result.target_label.title()} averaged {_fmt(result.mean_low, result.target_label)} "
        f"on {result.low_bucket or 'low'} days, compared with "
        f"{_fmt(result.mean_high, result.target_label)} on {result.high_bucket or 'high'} days "
        f"(over a {result.lag_days}-day gap)."
    )


def build_description(result: PatternResult) -> str:
    """'What did we observe?' - cautious, personalised, direction-aware sentence."""
    if result.direction is None:
        return "We don't yet see a consistent association in your data."

    # Direction-aware, cautious templates. Each describes feature days -> target
    # outcome as an OBSERVATION, never as a cause.
    relation = result.n >= 14 and "tend" or "appear"
    templates = {
        ("sleep_energy", "positive"): (
            f"On nights you slept more, your energy {relation}ed to be higher the following day; "
            "after shorter nights it trended lower."
        ),
        ("sleep_energy", "negative"): (
            f"On nights you slept more, your energy {relation}ed to be lower the following day."
        ),
        ("screen_sleep", "negative"): (
            f"On days after late-night screen use, your sleep {relation}ed to be shorter."
        ),
        ("screen_sleep", "positive"): (
            f"On days after late-night screen use, your sleep {relation}ed to be longer."
        ),
        ("activity_mood", "positive"): (
            f"On days with more steps, your mood {relation}ed to be higher the next day."
        ),
        ("activity_mood", "negative"): (
            f"On days with more steps, your mood {relation}ed to be lower the next day."
        ),
        ("exercise_stress", "negative"): (
            f"On exercise days, your stress {relation}ed to be lower the next day."
        ),
        ("exercise_stress", "positive"): (
            f"On exercise days, your stress {relation}ed to be slightly higher the next day."
        ),
        ("hydration_energy", "positive"): (
            f"On days you drank more water, your energy {relation}ed to be higher the next day."
        ),
        ("hydration_energy", "negative"): (
            f"On days you drank more water, your energy {relation}ed to be lower the next day."
        ),
        ("food_energy", "positive"): (
            f"On days with healthier meals, your energy {relation}ed to be higher the next day."
        ),
        ("food_energy", "negative"): (
            f"On days with healthier meals, your energy {relation}ed to be lower the next day."
        ),
        ("caffeine_sleep", "negative"): (
            f"On days you had caffeine, your sleep that night {relation}ed to be shorter."
        ),
        ("caffeine_sleep", "positive"): (
            f"On days you had caffeine, your sleep that night {relation}ed to be longer."
        ),
    }
    return templates.get((result.pattern_type, result.direction), "We see an association between your "
                                                                   f"{result.feature_label} and {result.target_label}.")


def build_limitations(result: PatternResult) -> str:
    if result.n < 14:
        return LIMITATION_NOT_ENOUGH_DATA
    return LIMITATION_SMALL_SAMPLE