"""
Application configuration loaded from environment variables.

Default database is SQLite so the project runs locally without external setup.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the API and database connection."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="__",
    )

    # JWT signing (use a long random string in production)
    secret_key: str = Field(
        default="dev-only-change-in-production-use-openssl-rand-hex-32",
        description="HS256 secret for access tokens",
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours for local dev

    # SQLite by default. Example:
    # sqlite:///./finance_system.db
    database_url: str = "sqlite:///./finance_system.db"

    api_v1_prefix: str = "/api/v1"
    project_name: str = "Finance System API"

    @property
    def sqlalchemy_database_uri(self) -> str:
        """SQLAlchemy URL from environment."""
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton for dependency injection."""
    return Settings()
