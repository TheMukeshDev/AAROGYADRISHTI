"""Deterministic coach provider (Phase 6) - the zero-configuration default.

This provider writes a genuine, structured reply from the user's OWN aggregate
data (patterns, experiments, learnings, next action). It never fabricates
numbers and never claims medical effect. It is the default so the feature works
out-of-the-box and so tests are deterministic.
"""

from __future__ import annotations

from app.ai.base_provider import CoachContext, CoachProvider

_DISCLAIMER = (
    "\n\nRemember: I am a lifestyle observation coach, not a doctor. "
    "I only describe associations in your own data - not causes, and not medical advice."
)


def _greeting(name: str | None, has_data: bool) -> str:
    if name:
        return f"Thanks for checking in{', ' + name if name else ''}."
    return "Thanks for checking in."


def _pattern_lines(context: CoachContext) -> list[str]:
    lines = []
    for p in context.patterns[:3]:
        if p.get("pattern_id", "").endswith("_energy"):
            direction = "higher energy"
        elif p.get("pattern_id") == "screen_sleep":
            direction = "longer sleep"
        elif p.get("pattern_id") == "activity_mood":
            direction = "better mood"
        else:
            direction = "an improvement"
        strength = p.get("strength_label", "early")
        corr = p.get("correlation")
        corr_txt = f" (correlation {corr:.2f} in your data)" if isinstance(corr, (int, float)) else ""
        lines.append(f"- Your data currently shows that {p.get('feature_label', 'your routines')} "
                     f"tend to line up with {p.get('target_label', 'your wellbeing')} - "
                     f"{strength}{corr_txt}.")
    return lines


def _experiment_lines(context: CoachContext) -> list[str]:
    lines = []
    if context.active_experiment:
        exp = context.active_experiment
        lines.append(
            f"- You have an active {exp.get('duration_days', 7)}-day experiment: "
            f"\"{exp.get('intervention', exp.get('title', ''))}\"."
        )
    for exp in context.recent_experiments[:2]:
        level = exp.get("evidence_level", "INSUFFICIENT")
        lines.append(
            f"- A recent experiment left you with {level.replace('_', ' ').lower()} evidence "
            f"about \"{exp.get('intervention', exp.get('title', ''))}\"."
        )
    return lines


def _learning_lines(context: CoachContext) -> list[str]:
    lines = []
    for learning in context.learnings[:2]:
        lines.append(
            f"- {learning.get('summary', '')}"
        )
    return lines


def _next_action_text(context: CoachContext) -> str:
    action = context.next_action or {}
    if not action:
        return "The next most useful step is to keep logging your daily check-ins."
    action_type = action.get("action_type", "collect_more_data")
    text = action.get("reason", "")
    heading = action.get("heading", "")
    return f"{heading}. {text}" if heading else text


def generate_deterministic_reply(context: CoachContext, user_text: str) -> str:
    sections: list[str] = [_greeting(context.user_name, context.has_daily_data)]

    if not context.has_daily_data and not context.patterns:
        return (
            "Thanks for checking in. I don't have much of your data yet - keep completing your "
            "daily check-ins and I'll be able to show what your habits look like."
        ) + _DISCLAIMER

    if user_text.strip():
        sections.append(f"I hear you: \"{user_text.strip()[:160]}\".")

    pattern_lines = _pattern_lines(context)
    if pattern_lines:
        sections.append("A quick look at your own patterns:")
        sections.append("\n".join(pattern_lines))

    exp_lines = _experiment_lines(context)
    if exp_lines:
        sections.append("Your experiments:")
        sections.append("\n".join(exp_lines))

    learning_lines = _learning_lines(context)
    if learning_lines:
        sections.append("What your personal profile say:" + "".join(f"\n{line}" for line in learning_lines))

    sections.append(f"Suggested next step: {_next_action_text(context)}")
    return "\n\n".join(sections) + _DISCLAIMER


class DeterministicCoachProvider(CoachProvider):
    name = "deterministic"

    def generate(self, messages: list[dict], context: CoachContext) -> str:
        user_lines = [m["content"] for m in messages if m.get("role") == "user"]
        user_text = user_lines[-1] if user_lines else ""
        return generate_deterministic_reply(context, user_text)