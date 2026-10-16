from functools import lru_cache
from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central application configuration.
    Values are loaded from environment variables and the .env file.
    """

    APP_NAME: str = "AeroLink Backend"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"

    MONGODB_URI: str | None = None
    MONGODB_DATABASE: str = "aerolink"

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
