"""Application configuration."""

import os
from functools import lru_cache


class Settings:
  def __init__(self) -> None:
    self.database_url: str = os.getenv(
      "DATABASE_URL",
      "sqlite+aiosqlite:///./deepflow.db",
    )
    self.database_url_sync: str = os.getenv(
      "DATABASE_URL_SYNC",
      self.database_url.replace("+aiosqlite", "").replace("+asyncpg", "+psycopg2"),
    )
    if self.database_url_sync == self.database_url and "sqlite" in self.database_url:
      self.database_url_sync = self.database_url.replace("+aiosqlite", "")


@lru_cache
def get_settings() -> Settings:
  return Settings()
