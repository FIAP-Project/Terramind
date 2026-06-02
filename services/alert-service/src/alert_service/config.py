"""Configuração do alert-service."""

from __future__ import annotations

from functools import lru_cache

from terramind_shared.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    service_name: str = "alert-service"
    db_schema: str = "alert"
    # Regras de exemplo (limiares de fallback se não houver Crop cadastrada).
    fallback_humidity_min: float = 30.0
    fallback_humidity_max: float = 80.0
    fallback_temp_min: float = 5.0
    fallback_temp_max: float = 40.0


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
