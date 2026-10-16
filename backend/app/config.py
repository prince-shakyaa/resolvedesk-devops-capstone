from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, loaded from environment variables or a local .env file."""

    app_name: str = "ResolveDesk API"
    environment: str = "local"
    database_url: str = "postgresql+psycopg://resolvedesk:resolvedesk@localhost:5432/resolvedesk"
    log_level: str = "info"
    cors_origins: list[str] = ["*"]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
