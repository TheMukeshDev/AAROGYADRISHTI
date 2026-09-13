"""Authentication request/response schemas."""

from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

_EMAIL_RE = re.compile(r"^\S+@\S+\.\S+$")

_PASSWORD_MIN = 8


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=_PASSWORD_MIN, max_length=128)

    @field_validator("password", mode="after")
    @classmethod
    def _validate_password(cls, value: str) -> str:
        if value.isdigit() or value.isalpha():
            raise ValueError("Password must mix letters, numbers or symbols.")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class FirebaseAuthRequest(BaseModel):
    id_token: str = Field(min_length=1, max_length=8192)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class RefreshTokenRequest(BaseModel):
    """Refresh tokens travel in the request body, never in the URL.

    Query parameters leak into access logs, proxy logs and browser history;
    a refresh token grants full session renewal, so it must stay out of them.
    """

    refresh_token: str = Field(min_length=1, max_length=4096)


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=_PASSWORD_MIN, max_length=128)

    @field_validator("new_password", mode="after")
    @classmethod
    def _validate_password(cls, value: str) -> str:
        if value.isdigit() or value.isalpha():
            raise ValueError("Password must mix letters, numbers or symbols.")
        return value


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: int
    email: str
    name: str | None = None
    email_verified: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class AuthStatusResponse(BaseModel):
    authenticated: bool
    user: UserResponse | None = None


TokenResponse.model_rebuild()