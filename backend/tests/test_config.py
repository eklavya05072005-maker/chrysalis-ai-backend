"""Tests for application settings and configuration security."""

from pydantic import SecretStr
from backend.app.core.config import Settings


def test_default_settings():
    settings = Settings()
    assert settings.app_name == "Chrysalis AI Engine"
    assert settings.llm_provider in ["gemini", "mock"]
    assert settings.gemini_model == "gemini-2.0-flash"
    assert settings.llm_timeout_seconds >= 5.0
    assert 0.0 <= settings.llm_temperature <= 1.0


def test_secret_masking():
    secret_key = "super-secret-production-key-12345"
    settings = Settings(gemini_api_key=SecretStr(secret_key))

    # Ensure raw secret is never displayed in str or repr
    assert secret_key not in str(settings.gemini_api_key)
    assert secret_key not in repr(settings.gemini_api_key)
    assert secret_key not in repr(settings)

    # Ensure secret is still accessible when explicitly requested
    assert settings.gemini_api_key.get_secret_value() == secret_key


def test_environment_override():
    settings = Settings(
        environment="test",
        gemini_model="gemini-1.5-pro",
        llm_timeout_seconds=45.0,
        llm_temperature=0.7,
    )
    assert settings.is_testing is True
    assert settings.is_production is False
    assert settings.gemini_model == "gemini-1.5-pro"
    assert settings.llm_timeout_seconds == 45.0
    assert settings.llm_temperature == 0.7
