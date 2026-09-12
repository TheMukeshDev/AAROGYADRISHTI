"""Application configuration.

All configuration is read from environment variables (see `.env.example`).
Nothing in this project may hardcode secrets - import `get_settings()` instead.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

AuthProviderName = Literal["jwt", "firebase"]


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
    jwt_secret: str = "change-me-to-a-64-char-random-string"
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "aarogyadrishti-api"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30
    password_reset_expire_minutes: int = 30
    password_min_length: int = 8

    # Firebase (only used when auth_provider == "firebase")
    firebase_project_id: str = ""
    firebase_credentials_path: str = ""

    # --- CORS --------------------------------------------------------------
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:8080"])

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
    allow_demo_data: bool = True
    demo_account_prefix: str = "demo"

    # --- AI coach (Phase 6) --------------------------------------------------
    # provider: "deterministic" (offline default) | "openai" | "openai_compatible"
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
