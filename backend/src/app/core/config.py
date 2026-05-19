from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.paths import setup_protocol_path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "DeepFlow Data API (P7)"
    api_v1_prefix: str = "/api/v1"
    storage_root: str = "./storage"
    database_url: str = "sqlite:///./storage/deepflow_p7.db"
    mock_mode: bool = True
    # Day1 dev: allow calls without JWT; set False before integration with P6 gateway
    dev_allow_anonymous: bool = True
    default_chunk_size: int = 5 * 1024 * 1024


setup_protocol_path()
settings = Settings()
