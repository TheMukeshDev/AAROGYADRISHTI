"""Production configuration guards - startup must refuse unsafe config."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def _prod(**overrides):
    # Safe defaults so they do not sneak in from the process environment, and
    # the individual guards are what we actually test.
    flags = {"debug": False, "allow_demo_data": False, "jwt_secret": "a" * 64}
    flags.update(overrides)
    return Settings(environment="production", **flags)


def test_production_requires_strong_jwt_secret():
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        _prod(jwt_secret="short")
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        _prod(jwt_secret="change-me-to-a-64-char-random-string")
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        _prod(jwt_secret="only-twenty-eight-chars-long")


def test_production_rejects_debug_true():
    with pytest.raises(ValidationError, match="DEBUG"):
        _prod(debug=True)


def test_production_rejects_demo_data():
    with pytest.raises(ValidationError, match="ALLOW_DEMO_DATA"):
        _prod(allow_demo_data=True)


def test_production_accepts_strong_secret_and_sane_flags():
    settings = _prod()
    assert settings.is_production
    assert settings.allow_demo_data is False


def test_demo_data_defaults_to_false(monkeypatch):
    # Guard against the known-password demo account being on by default.
    monkeypatch.delenv("ALLOW_DEMO_DATA", raising=False)
    settings = Settings(environment="development", jwt_secret="whatever")
    assert settings.allow_demo_data is False


def test_non_production_envs_are_not_guarded():
    # Local dev / tests must never trip the guards, even with the weak secret.
    settings = Settings(
        environment="development",
        jwt_secret="change-me-to-a-64-char-random-string",
        allow_demo_data=False,
    )
    assert settings.debug is True
    assert settings.is_production is False


def test_cors_origins_accepts_vercel_comma_separated_environment_value():
    settings = Settings(
        cors_origins="https://app.example, https://admin.example",
        jwt_secret="whatever",
    )

    assert settings.cors_origins == ["https://app.example", "https://admin.example"]