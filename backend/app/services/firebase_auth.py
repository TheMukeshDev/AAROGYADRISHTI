"""Firebase Admin token verification for provider sign-in."""

from __future__ import annotations

from typing import Any

from app.core.config import Settings
from app.core.errors import AuthenticationError, ServiceUnavailableError


def verify_id_token(id_token: str, settings: Settings) -> dict[str, Any]:
    """Verify a Firebase ID token and return its trusted claims."""
    try:
        import firebase_admin
        from firebase_admin import auth, credentials
    except ImportError as exc:  # pragma: no cover - dependency is runtime-only
        raise ServiceUnavailableError("Firebase authentication is not installed.") from exc

    try:
        try:
            firebase_app = firebase_admin.get_app()
        except ValueError:
            if settings.firebase_client_email and settings.firebase_private_key:
                service_account = {
                    "type": "service_account",
                    "project_id": settings.firebase_project_id,
                    "private_key": settings.firebase_private_key.replace("\\n", "\n"),
                    "client_email": settings.firebase_client_email,
                    "token_uri": settings.firebase_token_uri,
                }
                firebase_credential = credentials.Certificate(service_account)
            elif settings.firebase_credentials_path:
                firebase_credential = credentials.Certificate(settings.firebase_credentials_path)
            else:
                firebase_credential = credentials.ApplicationDefault()
            firebase_app = firebase_admin.initialize_app(
                firebase_credential,
                {"projectId": settings.firebase_project_id} if settings.firebase_project_id else None,
            )
        claims = auth.verify_id_token(id_token, app=firebase_app)
    except (ValueError, TypeError) as exc:
        raise ServiceUnavailableError("Firebase authentication is not configured correctly.") from exc
    except Exception as exc:  # Firebase SDK exposes provider-specific exception classes.
        raise AuthenticationError("The Google sign-in token is invalid or expired.") from exc

    if settings.firebase_project_id and claims.get("aud") != settings.firebase_project_id:
        raise AuthenticationError("The Google sign-in token belongs to another project.")
    if not claims.get("email") or not claims.get("email_verified"):
        raise AuthenticationError("A verified Google email address is required.")
    return claims