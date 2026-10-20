"""Application configuration and production settings."""

import logging
import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    app_name: str = Field(
        default="Hotel Booking System",
        validation_alias="APP_NAME",
        description="Name of the application",
    )
    environment: str = Field(
        default="development",
        validation_alias="ENVIRONMENT",
        description="Deployment environment (development, test, production)",
    )
    database_url: str = Field(
        default="sqlite:///hotel.db",
        validation_alias="DATABASE_URL",
        description="Database connection URL",
    )
    log_level: str = Field(
        default="INFO",
        validation_alias="LOG_LEVEL",
        description="Logging level",
    )
    api_host: str = Field(
        default="0.0.0.0",
        validation_alias="API_HOST",
        description="Host interface for API server",
    )
    api_port: int = Field(
        default=8000,
        validation_alias="API_PORT",
        description="Port for API server",
    )
    secret_key: str = Field(
        default="insecure-dev-secret-key-change-in-production",
        validation_alias="SECRET_KEY",
        description="Application secret key",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    # Check if APP_ENV was used as an alternate variable name
    if "APP_ENV" in os.environ and "ENVIRONMENT" not in os.environ:
        os.environ["ENVIRONMENT"] = os.environ["APP_ENV"]
    return Settings()


def setup_logging(settings: Settings | None = None) -> None:
    """Configure structured logging for production."""
    current_settings = settings or get_settings()
    level_name = current_settings.log_level.upper()
    numeric_level = getattr(logging, level_name, logging.INFO)

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )
