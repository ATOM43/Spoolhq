"""Settings from ``APP_*`` environment variables or the repository's ``.env`` file."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", env_file=ENV_FILE, extra="ignore")

    database_url: str = "sqlite:///./app.db"


@lru_cache
def get_settings() -> Settings:
    return Settings()
