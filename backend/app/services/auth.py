"""Auth orchestration service.

Kept as a thin module around the security helpers so the business rules live
in one place and the auth provider (JWT today, Firebase tomorrow) stays swappable.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import AuthenticationError, BadRequestError, ConflictError
from app.core.security import (
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    decode_token,
    hash_password,
    password_problems,
    verify_password,
)
from app.models.daily_log import DailyLog
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import RegisterRequest

users = UserRepository()


def _settings() -> Settings:
    return get_settings()


def register(db: Session, payload: RegisterRequest) -> tuple[User, str, str]:
    """Create a user (email/password) and return ``(user, access, refresh)``."""
    email = payload.email.lower().strip()
    if users.get_by_email(db, email) is not None:
        raise ConflictError("An account with this email already exists.")

    user = User(
        email=email,
        name=payload.name.strip(),
        password_hash=hash_password(payload.password),
        auth_provider="jwt",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access, _ = create_access_token(user.id, user.token_version, _settings())
    refresh, _ = create_refresh_token(user.id, user.token_version, _settings())
    return user, access, refresh


def authenticate(db: Session, email: str, password: str) -> tuple[User, str, str]:
    """Verify credentials and return ``(user, access, refresh)``."""
    user = users.get_by_email(db, email.lower().strip())
    if user is None or not verify_password(password, user.password_hash):
        raise AuthenticationError("Incorrect email or password.")
    access, _ = create_access_token(user.id, user.token_version, _settings())
    refresh, _ = create_refresh_token(user.id, user.token_version, _settings())
    return user, access, refresh


def refresh_access_token(db: Session, refresh_token: str) -> tuple[User, str, str]:
    claims = decode_token(refresh_token, _settings(), "refresh")
    user = db.get(User, int(claims.subject))
    if user is None or user.token_version != claims.token_version:
        raise AuthenticationError("This session is no longer valid. Please sign in again.")
    access, _ = create_access_token(user.id, user.token_version, _settings())
    new_refresh, _ = create_refresh_token(user.id, user.token_version, _settings())
    return user, access, new_refresh


def logout(db: Session, user: User) -> None:
    """Invalidate outstanding JWTs by bumping the token version."""
    user.token_version += 1
    db.commit()


def request_password_reset(db: Session, email: str) -> tuple[User, str]:
    """Return the reset token; does not send email in Phase 1 (no SMTP)."""
    user = users.get_by_email(db, email.lower().strip())
    if user is None:
        raise BadRequestError("No account found with this email.")
    token, _ = create_password_reset_token(user.id, user.token_version, _settings())
    return user, token


def reset_password(db: Session, token: str, new_password: str) -> User:
    settings = _settings()
    problems = password_problems(new_password, settings.password_min_length)
    if problems:
        raise BadRequestError(problems[0])
    claims = decode_token(token, settings, "password_reset")
    user = db.get(User, int(claims.subject))
    if user is None or user.token_version != claims.token_version:
        raise AuthenticationError("This reset link has expired. Please try again.")
    user.password_hash = hash_password(new_password)
    user.token_version += 1  # invalidate all old tokens
    db.commit()
    db.refresh(user)
    return user


def demo_seed_for(db: Session, user: User) -> None:
    """Seed 7 days of clearly-labelled demo daily logs (dev + demo accounts only)."""
    from datetime import date, timedelta

    today = date.today()
    demo_pattern = [
        dict(sleep_hours=7.1, steps=8423, active_minutes=38, exercise_level="moderate", water_liters=2.1, meal_quality="mixed", mood="good", energy=7, stress=2, caffeine="low", late_night_screen=False),
        dict(sleep_hours=6.2, steps=4305, active_minutes=14, exercise_level="none", water_liters=1.4, meal_quality="processed", mood="low", energy=5, stress=4, caffeine="moderate", late_night_screen=True),
        dict(sleep_hours=6.8, steps=6211, active_minutes=26, exercise_level="light", water_liters=1.8, meal_quality="healthy", mood="okay", energy=6, stress=3, caffeine="low", late_night_screen=False),
        dict(sleep_hours=7.6, steps=11204, active_minutes=54, exercise_level="intense", water_liters=2.6, meal_quality="healthy", mood="great", energy=8, stress=1, caffeine="low", late_night_screen=False),
        dict(sleep_hours=5.9, steps=3810, active_minutes=9, exercise_level="none", water_liters=1.1, meal_quality="processed", mood="very_low", energy=4, stress=5, caffeine="high", late_night_screen=True),
        dict(sleep_hours=7.3, steps=7412, active_minutes=32, exercise_level="moderate", water_liters=2.2, meal_quality="mixed", mood="good", energy=7, stress=2, caffeine="moderate", late_night_screen=False),
        dict(sleep_hours=7.0, steps=6530, active_minutes=22, exercise_level="light", water_liters=1.9, meal_quality="mixed", mood="okay", energy=6, stress=3, caffeine="low", late_night_screen=True),
    ]
    for i, values in enumerate(demo_pattern):
        offset = 6 - i
        day = today - timedelta(days=offset)
        existing = db.scalars(
            select(DailyLog).where(DailyLog.user_id == user.id, DailyLog.date == day)
        ).first()
        if existing is not None:
            continue
        db.add(DailyLog(user_id=user.id, source="demo", date=day, **values))
    db.commit()
