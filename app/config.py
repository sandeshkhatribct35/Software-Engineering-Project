"""Application settings.

All environment-specific values are read from the environment so that the same
image runs unchanged locally, in Docker and in CI (GUIDE NFR-9). The defaults
below describe a local development database only; no real credential is ever
stored in source (GUIDE NFR-10).
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

LOCAL_DATABASE_URL = "postgresql+psycopg://fairshare:fairshare@localhost:5432/fairshare"


class Settings(BaseSettings):
    """Runtime configuration resolved from environment variables or a .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = LOCAL_DATABASE_URL
    log_level: str = "INFO"
    echo_sql: bool = False


@lru_cache
def get_settings() -> Settings:
    """Return the cached settings instance.

    Caching keeps a single source of configuration for the process; tests reset
    the cache when they need to point the application at the test database.
    """
    return Settings()
