"""Coach safety guard (Phase 6, section 5).

Everything the coach says is limited to lifestyle observations. This module:

- strips phone-number-like digit runs from replies,
- replaces medication/dosage phrasing (e.g. "take 500 mg") with a correction,
- blocks the coach from promising results or making causal claims,
- appends the standard non-medical disclaimer when it is missing.
"""

from __future__ import annotations

import re

_DISCLAIMER = (
    "I am a lifestyle observation coach, not a doctor. I describe associations in your own "
    "data - never causes, diagnoses, or treatment plans."
)

_PHONE_PATTERN = re.compile(r"(?<!\d)\d{7,}(?!\d)")
# Medication-style phrasing: a number followed by a dose unit.
_DOSAGE_PATTERN = re.compile(r"\b\d{1,4}\s*(?:mg|mcg|mcg)\b", re.IGNORECASE)
_CAUSAL_CLAIM_PATTERN = re.compile(
    r"\b(?:will (?:cure|fix|prevent|stop your|make you)|guarantee(?:d)?)\b",
    re.IGNORECASE,
)

_BLOCKED_TOPICS = ("prescription", "prescribed dosage", "diagnos")


def sanitize_coach_reply(text: str, role: str = "coach") -> str:
    """Apply the safety rules to a coach reply."""
    if not text:
        return text
    clean = text

    if role == "coach":
        clean = _PHONE_PATTERN.sub("[contact hidden]", clean)
        clean = _DOSAGE_PATTERN.sub("a dose prescribed only by a clinician", clean)
        clean = _CAUSAL_CLAIM_PATTERN.sub("might be associated with", clean)

    # Never let a coach reply assert blocked topics.
    lowered = clean.lower()
    for topic in _BLOCKED_TOPICS:
        if topic in lowered:
            clean = clean.replace(topic, "medication advice")

    if "not a doctor" not in clean.lower():
        clean = f"{clean}\n\n{_DISCLAIMER}"
    return clean


def is_prohibited_user_question(text: str) -> bool:
    """Whether a user question is outside the coach's scope (requires refusal)."""
    lowered = text.lower()
    return any(
        phrase in lowered
        for phrase in (
            "what medicine", "what medication", "should i take", "dosage", "treat my disease",
            "diagnose", "prescription",
        )
    )