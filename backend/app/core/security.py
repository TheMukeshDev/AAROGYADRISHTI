"""Password hashing and JWT helpers.

Password hashing uses the *bcrypt-sha256* scheme: the password is first
digested with SHA-256 (hex) and that digest is bcrypt-hashed. This keeps
bcrypt's 72-byte input limit irrelevant while preserving bcrypt's cost factor.
The scheme is stored as a prefix so future migrations (e.g. to Argon2) can be
detected and re-hashed on next successful login.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal

import bcrypt
import jwt
from jwt import InvalidTokenError

from app.core.config import Settings

TokenType = Literal["access", "refresh", "password_reset"]

_BCRYPT_SCHEME = "bcrypt-sha256"
_BCRYPT_ROUNDS = 12
_PREHASH_SALT = b"aarogyadrishti.v1"  # static application-level pepper domain


class TokenError(Exception):
    """Raised when a token is missing, malformed, expired or of wrong type."""


# ---------------------------------------------------------------------------
# Passwords
# ---------------------------------------------------------------------------
def _prehash(password: str) -> bytes:
    digest = hashlib.sha256(_PREHASH_SALT + password.encode("utf-8")).hexdigest()
    return digest.encode("ascii")


def hash_password(password: str) -> str:
    """Return a storable password hash (never store the plain password)."""
    hashed = bcrypt.hashpw(_prehash(password), bcrypt.gensalt(rounds=_BCRYPT_ROUNDS))
    return f"{_BCRYPT_SCHEME}${hashed.decode('ascii')}"


def verify_password(password: str, stored_hash: str | None) -> bool:
    """Constant-time-ish verification of a password against a stored hash."""
    if not stored_hash:
        return False
    scheme, _, digest = stored_hash.partition("$")
    if scheme != _BCRYPT_SCHEME or not digest:
        return False
    try:
        return bcrypt.checkpw(_prehash(password), digest.encode("ascii"))
    except (ValueError, TypeError):
        return False


def password_problems(password: str, min_length: int = 8) -> list[str]:
    """Return a list of human-readable password policy violations."""
    problems: list[str] = []
    if len(password) < min_length:
        problems.append(f"Password must be at least {min_length} characters long.")
    if password.isdigit() or password.isalpha():
        problems.append("Password must mix letters, numbers or symbols.")
    if password.strip() != password:
        problems.append("Password must not start or end with whitespace.")
    return problems


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class TokenClaims:
    """Decoded, validated claims."""

    subject: str
    token_type: TokenType
    token_version: int
    token_id: str
    expires_at: datetime


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _encode(subject: str, token_type: TokenType, token_version: int, settings: Settings, lifetime: timedelta) -> tuple[str, datetime]:
    issued_at = _now()
    expires_at = issued_at + lifetime
    payload = {
        "sub": str(subject),  # PyJWT requires the subject to be a string
        "typ": token_type,
        "ver": token_version,
        "jti": str(uuid.uuid4()),
        "iss": settings.jwt_issuer,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, expires_at


def create_access_token(subject: str, token_version: int, settings: Settings) -> tuple[str, datetime]:
    return _encode(subject, "access", token_version, settings, timedelta(minutes=settings.access_token_expire_minutes))


def create_refresh_token(subject: str, token_version: int, settings: Settings) -> tuple[str, datetime]:
    return _encode(subject, "refresh", token_version, settings, timedelta(days=settings.refresh_token_expire_days))


def create_password_reset_token(subject: str, token_version: int, settings: Settings) -> tuple[str, datetime]:
    return _encode(subject, "password_reset", token_version, settings, timedelta(minutes=settings.password_reset_expire_minutes))


def decode_token(token: str, settings: Settings, expected_type: TokenType) -> TokenClaims:
    """Decode and validate a JWT. Raises :class:`TokenError` on any problem."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            options={"require": ["exp", "sub", "typ"]},
        )
    except InvalidTokenError as exc:  # expired, bad signature, malformed...
        raise TokenError("Invalid or expired token.") from exc

    token_type = payload.get("typ")
    if token_type != expected_type:
        raise TokenError("Unexpected token type.")

    subject = payload.get("sub")
    if not subject:
        raise TokenError("Token is missing a subject.")

    return TokenClaims(
        subject=str(subject),
        token_type=token_type,
        token_version=int(payload.get("ver", 0)),
        token_id=str(payload.get("jti", "")),
        expires_at=datetime.fromtimestamp(int(payload["exp"]), tz=timezone.utc),
    )
