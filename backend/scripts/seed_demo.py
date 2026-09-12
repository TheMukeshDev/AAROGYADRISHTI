"""Seed clearly-labelled demo data for hackathon/UI testing.

Creates (if needed) a ``demo`` user and 7 days of realistic lifestyle check-ins
marked ``source="demo"``. Never runs against production (guarded by
``ALLOW_DEMO_DATA``). Run from ``backend/``:

    python -m scripts.seed_demo
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import get_settings  # noqa: E402
from app.database.session import SessionLocal  # noqa: E402
from app.services.demo import seed_demo_user  # noqa: E402


def main() -> None:
    settings = get_settings()
    if not settings.allow_demo_data:
        print("Demo seeding is disabled (ALLOW_DEMO_DATA=false).")
        return
    with SessionLocal() as db:
        user, _, _ = seed_demo_user(db)
        print(f"Demo user ready: {user.email} (is_demo={user.is_demo})")


if __name__ == "__main__":
    main()