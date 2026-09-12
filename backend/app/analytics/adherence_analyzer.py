"""Intervention adherence (Phase 4, analytics module #4).

How often the user reported meeting the experiment's daily target
(e.g. sleep >= 7h). Distinguishes "the intervention was followed" from
"the outcome changed". Adherence is never interpreted as a health success.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AdherenceResult:
    days_met: int
    days_total: int
    adherence: float | None      # 0..100 or None when no target data logged
    text: str


def analyze_adherence(days_total: int, target_met_flags: list[bool | None]) -> AdherenceResult:
    if days_total <= 0:
        return AdherenceResult(days_met=0, days_total=0, adherence=None, text="No experiment days to measure.")
    met = sum(1 for flag in target_met_flags if flag is True)
    adherence = round((met / days_total) * 100.0, 1) if target_met_flags else None
    if adherence is None:
        text = "Target adherence could not be measured yet."
    else:
        text = f"Target met on {met} of {days_total} days."
    return AdherenceResult(days_met=met, days_total=days_total, adherence=adherence, text=text)