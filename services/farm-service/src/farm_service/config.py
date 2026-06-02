"""Configuração do farm-service."""

from __future__ import annotations

from functools import lru_cache

from terramind_shared.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    service_name: str = "farm-service"
    db_schema: str = "farm"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
