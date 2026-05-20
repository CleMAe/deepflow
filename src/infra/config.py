"""Canonical application configuration — single source of truth for all modules."""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


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
    jwt_secret_key: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # Dev mode
    mock_mode: bool = True
    dev_allow_anonymous: bool = True

    # Upload
    default_chunk_size: int = 5 * 1024 * 1024  # 5 MiB


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Module-level singleton for direct import
settings = get_settings()
