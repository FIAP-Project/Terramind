"""Entry point do farm-service."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from farm_service.config import get_settings
from farm_service.controllers import crop_router, farm_router, plot_router
from terramind_shared.app import apply_standard_middleware
from terramind_shared.db import Database
from terramind_shared.events import EventBus
from terramind_shared.security import JWTService

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
        title="Terramind — Farm Service",
        description="Gestão de fazendas, talhões e catálogo de culturas.",
        version="0.1.0",
        docs_url="/farm/docs",
        openapi_url="/farm/openapi.json",
        redoc_url=None,
        lifespan=lifespan,
    )
    apply_standard_middleware(app, settings.cors_allowed_origins)
    app.include_router(farm_router)
    app.include_router(plot_router)
    app.include_router(crop_router)

    @app.get("/farm/health", tags=["health"], summary="Liveness probe")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": settings.service_name}

    return app


app = create_app()
