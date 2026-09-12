"""Learning candidate lifecycle (Phase 4, section 14).

A candidate is an observation awaiting aggregation by the Phase 5 personal
learning profile. Users may accept or reject a candidate; the calculated
evidence values are never user-editable.
"""

from __future__ import annotations

from app.core.errors import ConflictError

_ALLOWED_TRANSITIONS = {
    # User actions. An accepted candidate is finalised (spec: no more edits),
    # and a rejected candidate can only be superseded by a newer experiment.
    "candidate": {"accepted", "rejected", "superseded"},
    "accepted": {"superseded"},
    "rejected": {"superseded"},
    "superseded": set(),
}


def transition_candidate(candidate, status: str) -> str:
    if status not in {"candidate", "accepted", "rejected", "superseded"}:
        raise ConflictError("Unknown candidate status.")
    allowed = _ALLOWED_TRANSITIONS.get(candidate.status, set())
    if status not in allowed:
        raise ConflictError(f"A candidate in state '{candidate.status}' cannot transition to '{status}'.")
    candidate.status = status
    return status