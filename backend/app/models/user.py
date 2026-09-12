"""User and user profile ORM models."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    email_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    auth_provider: Mapped[str] = mapped_column(String(20), default="jwt", nullable=False)
    # Incremented on logout / password reset to invalidate outstanding JWTs.
    token_version: Mapped[int] = mapped_column(default=0, nullable=False)
    is_demo: Mapped[bool] = mapped_column(default=False, nullable=False)

    profile: Mapped["UserProfile | None"] = relationship(
        back_populates="user", uselist=False, lazy="selectin", cascade="all, delete-orphan"
    )


class UserProfile(Base, TimestampMixin):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    age_group: Mapped[str | None] = mapped_column(String(30), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(30), nullable=True)
    height_cm: Mapped[float | None] = mapped_column(nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(nullable=True)
    activity_level: Mapped[str | None] = mapped_column(String(30), nullable=True)
    primary_goal: Mapped[str | None] = mapped_column(String(40), nullable=True)
    # Onboarding completion flag so the app can resume cleanly.
    onboarding_completed: Mapped[bool] = mapped_column(default=False, nullable=False)
    timeframe_start: Mapped[date | None] = mapped_column(Date, nullable=True)

    user: Mapped[User] = relationship(back_populates="profile")