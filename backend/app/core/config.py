"""Application configuration loaded from environment variables.

Centralizing settings in a single Pydantic ``BaseSettings`` object keeps
configuration explicit, typed, and testable (Dependency Inversion: the rest of
the app depends on this abstraction rather than reading ``os.environ`` directly).
"""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "LinkedIn Page Analytics Dashboard"
    api_v1_prefix: str = "/api"
    debug: bool = False

    # Database
    database_url: str = Field(
        default="postgresql+psycopg://linkedin:linkedin@db:5432/linkedin_analytics",
        description="SQLAlchemy database URL.",
    )

    # Uploads
    max_upload_bytes: int = 25 * 1024 * 1024  # 25 MB
    allowed_extensions: tuple[str, ...] = (".xls", ".xlsx")

    # CORS
    cors_origins: list[str] = ["*"]


@lru_cache
def get_settings() -> Settings:
    """Cached accessor so the env is parsed once per process."""
    return Settings()
