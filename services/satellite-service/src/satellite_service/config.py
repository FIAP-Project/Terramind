"""Configuração do satellite-service."""

from __future__ import annotations

from functools import lru_cache

from terramind_shared.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    service_name: str = "satellite-service"
    db_schema: str = "satellite"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
