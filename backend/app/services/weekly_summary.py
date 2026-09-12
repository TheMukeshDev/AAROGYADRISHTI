"""Weekly observation summary service (Phase 6).

Summarises the last N days from the user's OWN daily logs with simple counts and
averages - never compared against population numbers, never a diagnosis.
"""

from __future__ import annotations

import statistics
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analytics.config import AnalyticsConfig
from app.models.experiment import Experiment


def build_weekly_summary(db: Session, user_id: int, days: int = 7) -> dict:
    start = date.today() - timedelta(days=days - 1)
    from app.repositories.daily_log import DailyLogRepository

    logs = DailyLogRepository().list_in_range(db, user_id, start, date.today())
    tracked = len(logs)

    def _avg(field):
        values = [getattr(log, field) for log in logs if getattr(log, field) is not None]
        try:
            return {"value": round(statistics.mean(values), 1), "count": len(values)}
        except (statistics.StatisticsError, TypeError):
            return None

    completed = len(
        list(
            db.scalars(
                select(Experiment).where(
                    Experiment.user_id == user_id,
                    Experiment.status == "completed",
                )
            )
        )
    )

    return {
        "window_days": days,
        "days_tracked": tracked,
        "completion_rate": round(tracked / days, 2) if days else 0.0,
        "averages": {
            "sleep_hours": _avg("sleep_hours"),
            "steps": _avg("steps"),
            "energy": _avg("energy"),
            "stress": _avg("stress"),
        },
        "experiments_completed_total": completed,
        "generated_on": date.today().isoformat(),
    }


def build_weekly_summary_text(summary: dict) -> str:
    if not summary["days_tracked"]:
        return (
            "This week I have no check-ins from you yet - even a couple of daily logs "
            "would help me show your weekly rhythm. (Observation only - not medical advice.)"
        )
    parts = [f"You tracked {summary['days_tracked']} of {summary['window_days']} days this week."]
    aves = summary["averages"]
    if aves["sleep_hours"] and aves["sleep_hours"]["count"]:
        parts.append(
            f"Your sleep averaged {aves['sleep_hours']['value']}h on {aves['sleep_hours']['count']} nights."
        )
    if aves["energy"] and aves["energy"]["count"]:
        parts.append(
            f"Your energy averaged {aves['energy']['value']}/10 on {aves['energy']['count']} days."
        )
    parts.append(
        "These are observations from your own check-ins - not a diagnosis and not a predictor."
    )
    return " ".join(parts)