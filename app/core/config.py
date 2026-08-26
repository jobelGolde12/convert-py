from __future__ import annotations

import os
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Convert API"
    app_url: str = "http://localhost:8000"
    tagline: str = "Document conversion with style and substance"
    env: Literal["development", "staging", "production"] = "development"
    secret_key: str = "dev-secret-key-change-me"
    upload_secret: str = "dev-only-change-me"

    cors_origins: list[str] = []

    database_url: str = "sqlite:///./dev.db"
    redis_url: str = "redis://127.0.0.1:6379"

    # Turso / libSQL (optional — falls back to local SQLite when unset)
    turso_database_url: str = ""
    turso_auth_token: str = ""

    retention_anon_hours: int = 1

    anon_conversions_per_day: int = 5
    anon_req_per_min: int = 60

    lo_concurrency: int = 1
    lo_timeout_ms: int = 900_000
    lo_profile_root: str = "/tmp/lo-profiles"

    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket: str = "convert-files"
    r2_public_url: str = ""

    storage_backend: Literal["local", "r2", "s3"] = "local"
    local_storage_root: str = os.path.join(os.getcwd(), "storage")

    @property
    def upload_secret_is_default(self) -> bool:
        return not self.upload_secret or self.upload_secret == "dev-only-change-me"

    @property
    def is_prod(self) -> bool:
        return self.env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
