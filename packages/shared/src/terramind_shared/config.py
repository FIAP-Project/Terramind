"""Configuração base para todos os serviços.

Cada serviço herda de `BaseServiceSettings` e adiciona campos específicos.
Os valores são lidos de variáveis de ambiente (via Pydantic Settings).
"""

from __future__ import annotations

from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseServiceSettings(BaseSettings):
    """Configuração mínima compartilhada por todos os serviços."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Identificação
    service_name: str = "terramind-service"
    environment: str = "development"
    log_level: str = "INFO"

    # Banco de dados
    database_url: str = Field(
        default="postgresql+asyncpg://terramind:terramind_dev_password@postgres:5432/terramind",
        description="URL de conexão async do SQLAlchemy.",
    )
    db_schema: str = "public"

    # Mensageria
    amqp_url: str = Field(
        default="amqp://terramind:terramind_dev_password@rabbitmq:5672/",
        description="URL de conexão do RabbitMQ.",
    )
    event_signing_secret: str = Field(
        default="please-change-32-char-minimum-secret-for-hmac",
        min_length=32,
        description="Segredo HMAC para assinatura de eventos (mín 32 chars).",
    )

    # JWT
    jwt_secret: str = Field(
        default="please-change-32-char-minimum-secret-12345",
        min_length=32,
        description="Segredo HS256 do JWT (mín 32 chars).",
    )
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 7

    # HTTP / CORS
    cors_allowed_origins: list[str] = Field(default_factory=lambda: ["https://localhost:8443"])

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def _split_cors(cls, value: Any) -> Any:
        """Aceita string separada por vírgula ou lista."""
        if isinstance(value, str):
            return [o.strip() for o in value.split(",") if o.strip()]
        return value
