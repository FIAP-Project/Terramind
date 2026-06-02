"""Composição de middleware padrão para os serviços.

Cada `create_app()` chama `apply_standard_middleware(app, settings.cors_allowed_origins)`
para garantir o mesmo stack: RequestId → SecurityHeaders → CORS → handlers de erro.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from terramind_shared.middleware import (
    RequestIdMiddleware,
    SecurityHeadersMiddleware,
    register_exception_handlers,
)


def apply_standard_middleware(app: FastAPI, cors_allowed_origins: list[str]) -> None:
    """Aplica middlewares padrão e handlers de erro a um FastAPI app."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(app)
