"""Application configuration.

All configuration is read from environment variables (see `.env.example`).
Nothing in this project may hardcode secrets - import `get_settings()` instead.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

AuthProviderName = Literal["jwt", "firebase"]

# The default value is publicly known (it is committed in this repository), so
# it must NEVER be used to sign tokens when serving real traffic.
_DEFAULT_JWT_SECRET = "change-me-to-a-64-char-random-string"


class Settings(BaseSettings):
    """Typed settings object.

    Field names map to upper-case environment variables, e.g. ``database_url``
    is populated from ``DATABASE_URL``.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Application -------------------------------------------------------
    app_name: str = "AarogyaDrishti API"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    # --- Database ----------------------------------------------------------
    # Default points at local PostgreSQL; tests override with SQLite in-memory.
    database_url: str = "postgresql+psycopg://aarogya:aarogya@localhost:5432/aarogyadrishti"
    db_echo: bool = False
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # --- Authentication ----------------------------------------------------
    auth_provider: AuthProviderName = "jwt"
    # The default is intentionally obvious and must be overridden before any
    # real deployment - see the production guard below.
    jwt_secret: str = _DEFAULT_JWT_SECRET
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "aarogyadrishti-api"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30
    password_reset_expire_minutes: int = 30
    password_min_length: int = 8

    # Firebase (used by the Google sign-in token exchange)
    firebase_project_id: str = ""
    firebase_credentials_path: str = ""
    firebase_client_email: str = ""
    firebase_private_key: str = ""
    firebase_token_uri: str = "https://oauth2.googleapis.com/token"

    # --- CORS --------------------------------------------------------------
    cors_origins: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["http://localhost:8080"])

    # --- Rate limiting ------------------------------------------------------
    # Disabled by default so local dev and the test suite are unaffected.
    # Production deployments SHOULD enable it (and normally run a second layer
    # at the gateway/reverse-proxy). Limits are per-IP and in-memory - a single
    # process. Behind a proxy set TRUSTED_PROXY_COUNT accordingly.
    rate_limit_enabled: bool = False
    rate_limit_general_per_minute: int = 120
    rate_limit_auth_per_minute: int = 10
    rate_limit_trusted_proxy_count: int = 0

    # --- Baseline (Phase 1) ------------------------------------------------
    baseline_target_days: int = 7
    baseline_window_days: int = 14

    # --- Experiments (Phase 3) ---------------------------------------------
    experiment_cooldown_days: int = 14          # min days between repeats of the same experiment
    experiment_baseline_window_days: int = 14   # how far back the before-period looks
    experiment_min_baseline_days: int = 3

    # --- Evidence (Phase 4) ---------------------------------------------------
    evidence_min_observations: int = 3
    evidence_min_completeness: float = 0.5
    evidence_min_effect_magnitude: float = 0.3
    evidence_consistency_threshold: float = 0.6
    evidence_repeat_min_experiments: int = 2

    # --- Demo data ---------------------------------------------------------
    allow_demo_data: bool = False
    demo_account_prefix: str = "demo"

    # --- AI coach (Phase 6) --------------------------------------------------
    # provider: "deterministic" | "gemini" | "openai_compatible"
    ai_provider: str = "deterministic"
    ai_api_key: str = ""
    ai_base_url: str = ""            # e.g. https://api.openai.com/v1
    ai_model: str = "gpt-4o-mini"
    ai_request_timeout_seconds: int = 45
    ai_max_coach_number: int = 80        # chars; the coach never types phone-like groups

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        """Allow ``CORS_ORIGINS`` to be a comma separated string."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("database_url", mode="before")
    @classmethod
    def _use_psycopg3_driver(cls, value: object) -> object:
        """Use the installed psycopg 3 driver for generic PostgreSQL URLs."""
        if isinstance(value, str):
            if value.startswith("postgresql://"):
                return value.replace("postgresql://", "postgresql+psycopg://", 1)
            if value.startswith("postgres://"):
                return value.replace("postgres://", "postgresql+psycopg://", 1)
        return value

    @model_validator(mode="after")
    def _production_guards(self) -> "Settings":
        """Fail fast (at startup, not at request time) on unsafe production config.

        These guards only trigger when ``ENVIRONMENT=production`` so local dev
        and the test suite are never affected. Prefer crashing loudly over
        silently serving real health data with a weak secret.
        """
        if self.environment != "production":
            return self

        if self.debug:
            raise ValueError(
                "DEBUG must be false in production: the interactive API docs "
                "(/docs, /redoc, openapi.json) would be exposed."
            )
        if self.allow_demo_data:
            raise ValueError(
                "ALLOW_DEMO_DATA must be false in production: the demo endpoints "
                "create accounts with a well-known password and seeded health data."
            )
        if len(self.jwt_secret) < 32 or self.jwt_secret == _DEFAULT_JWT_SECRET:
            raise ValueError(
                "JWT_SECRET is missing or too weak. Generate one with e.g. "
                "`python -c \"import secrets; print(secrets.token_urlsafe(64))\"` "
                "and set it BEFORE starting the API in production."
            )
        if self.auth_provider == "firebase" and not self.firebase_project_id:
            raise ValueError("FIREBASE_PROJECT_ID is required when AUTH_PROVIDER=firebase.")
        if self.auth_provider == "firebase" and not (
            self.firebase_credentials_path
            or (self.firebase_client_email and self.firebase_private_key)
        ):
            raise ValueError(
                "Set Firebase service-account fields on Vercel or "
                "FIREBASE_CREDENTIALS_PATH when AUTH_PROVIDER=firebase."
            )
        return self

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings singleton."""
    return Settings()
