"""Canonical application configuration — single source of truth for all modules."""

from __future__ import annotations

from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_JWT_SECRET_KEY = "dev-secret-change-in-production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "DeepFlow"
    api_v1_prefix: str = "/api/v1"

    # Database — sync SQLAlchemy URL (Day1 default; async engine TBD)
    database_url: str = "sqlite:///./deepflow.db"

    # Storage
    storage_root: str = "./storage"

    # Auth
    jwt_secret_key: str = Field(
        default=DEFAULT_JWT_SECRET_KEY,
        validation_alias=AliasChoices("JWT_SECRET_KEY", "JWT_SECRET"),
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # Dev mode
    mock_mode: bool = True
    dev_allow_anonymous: bool = True

    # LLM / Agent
    llm_default_provider: str = "mock"
    llm_default_model: str = "gpt-4"
    llm_api_key: str = ""
    llm_api_base: str = ""
    agent_max_tool_rounds: int = 5
    agent_max_history_messages: int = 50

    # Upload
    default_chunk_size: int = 5 * 1024 * 1024  # 5 MiB


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Module-level singleton for direct import
settings = get_settings()
