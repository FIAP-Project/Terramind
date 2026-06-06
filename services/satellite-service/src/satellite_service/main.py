"""Entry point do satellite-service."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from terramind_shared.app import apply_standard_middleware
from terramind_shared.db import Database
from terramind_shared.events import EventBus
from terramind_shared.security import JWTService

from satellite_service.config import get_settings
from satellite_service.controllers import reading_router, satellite_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logging.basicConfig(level=settings.log_level.upper())

    app.state.settings = settings
    app.state.database = Database(settings.database_url)
    app.state.event_bus = EventBus(settings.amqp_url, settings.event_signing_secret)
    app.state.jwt_service = JWTService(
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
        access_ttl_minutes=settings.access_token_ttl_minutes,
        refresh_ttl_days=settings.refresh_token_ttl_days,
    )

    try:
        await app.state.event_bus.connect()
    except Exception:
        logger.exception("event bus connect failed; continuing without it")

    yield

    try:
        await app.state.event_bus.close()
    finally:
        await app.state.database.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Terramind — Satellite Service",
        description="Satélites e ingestão de leituras.",
        version="0.1.0",
        docs_url="/satellite/docs",
        openapi_url="/satellite/openapi.json",
        redoc_url=None,
        lifespan=lifespan,
    )
    apply_standard_middleware(app, settings.cors_allowed_origins)
    app.include_router(satellite_router)
    app.include_router(reading_router)

    @app.get("/satellite/health", tags=["health"], summary="Liveness probe")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": settings.service_name}

    return app


app = create_app()
