"""Demo-data seeding (development only).

Demo accounts are created with ``User.is_demo == True`` and seeded via
``auth.demo_seed_for``. Server-side seeding is guarded by ``ALLOW_DEMO_DATA``;
the Flutter app additionally offers a local demo mode so the same 7-day pattern
is available offline. Demo data is never mixed into real user metrics.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import ForbiddenError
from app.core.security import hash_password
from app.models.user import User
from app.repositories.user import UserRepository

users = UserRepository()


def seed_demo_user(db: Session, email: str | None = None, name: str | None = None) -> tuple[User, str, str]:
    """Create (or return an existing) demo user and seed 7 days of data.

    Returns ``(user, access, refresh)``. This endpoint exists for hackathon /
    UI testing only and is disabled in production via ``ALLOW_DEMO_DATA``.
    """
    settings = get_settings()
    if not settings.allow_demo_data or settings.is_production:
        raise ForbiddenError("Demo data seeding is disabled in this environment.")

    from app.services.auth import demo_seed_for

    email = (email or f"{settings.demo_account_prefix}@aarogyadrishti.local").lower().strip()
    user = users.get_by_email(db, email)
    if user is None:
        user = User(
            email=email,
            name=name or "Demo User",
            password_hash=hash_password("demo12345"),
            auth_provider="jwt",
            is_demo=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    demo_seed_for(db, user)
    return user, None, None