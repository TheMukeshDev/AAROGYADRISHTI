"""Shared FastAPI dependencies (current user, DB session)."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AuthenticationError
from app.core.security import TokenError, decode_token
from app.database.session import get_db
from app.models.user import User

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> User:
    if credentials is None:
        raise AuthenticationError("Authentication required.")
    try:
        claims: TokenClaims = decode_token(credentials.credentials, get_settings(), "access")
    except TokenError as exc:
        raise AuthenticationError("Your session has expired. Please sign in again.") from exc
    user = db.get(User, int(claims.subject))
    if user is None:
        raise AuthenticationError("This account no longer exists.")
    if user.token_version != claims.token_version:
        raise AuthenticationError("Your session has been invalidated. Please sign in again.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]