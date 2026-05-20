"""App-layer settings — delegates to canonical infra config with module-specific defaults."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict

# Re-export the canonical infra settings so existing imports keep working.
# P6 owns `src/infra/config.py` as the single source of truth for DB, auth, storage.
from src.infra.config import settings  # noqa: F401


class AppSettings(BaseSettings):
    """Module-specific settings that don't belong in the canonical infra layer.

    Only add settings here that are truly P7/P8-specific and should NOT
    be shared across all BE modules.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # No module-specific settings yet — all current settings live in infra config.
    pass
