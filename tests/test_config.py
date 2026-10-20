"""Tests for configuration settings and environment variable handling."""

import os
from unittest import mock

from hotel_booking.config import Settings, get_settings, setup_logging


def test_default_settings() -> None:
    """Verify default settings initialization."""
    settings = Settings()
    assert settings.app_name == "Hotel Booking System"
    assert settings.environment in {"development", "test", "production"}
    assert "sqlite" in settings.database_url
    assert settings.log_level == "INFO"
    assert settings.api_port == 8000
    assert settings.api_host == "0.0.0.0"
    assert len(settings.secret_key) > 0


def test_environment_override() -> None:
    """Test that environment variables successfully override default settings."""
    env_vars = {
        "APP_NAME": "Custom Hotel App",
        "ENVIRONMENT": "production",
        "DATABASE_URL": "sqlite:///custom_prod.db",
        "LOG_LEVEL": "WARNING",
        "API_PORT": "9000",
        "API_HOST": "127.0.0.1",
        "SECRET_KEY": "super-secret-production-token",
    }
    with mock.patch.dict(os.environ, env_vars, clear=False):
        settings = Settings()
        assert settings.app_name == "Custom Hotel App"
        assert settings.environment == "production"
        assert settings.database_url == "sqlite:///custom_prod.db"
        assert settings.log_level == "WARNING"
        assert settings.api_port == 9000
        assert settings.api_host == "127.0.0.1"
        assert settings.secret_key == "super-secret-production-token"


def test_app_env_alias() -> None:
    """Test APP_ENV compatibility alias."""
    get_settings.cache_clear()
    with mock.patch.dict(os.environ, {"APP_ENV": "staging"}, clear=False):
        if "ENVIRONMENT" in os.environ:
            del os.environ["ENVIRONMENT"]
        settings = get_settings()
        assert settings.environment == "staging"
    get_settings.cache_clear()


def test_setup_logging() -> None:
    """Test setup_logging does not fail with different log levels."""
    settings = Settings(log_level="DEBUG")
    setup_logging(settings)
    setup_logging(None)
