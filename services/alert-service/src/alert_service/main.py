"""Entry point do alert-service."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from alert_service.config import get_settings
from alert_service.consumer import start_consumer
from alert_service.controllers import alert_router
from alert_service.services.rule_engine import RuleEngine, Thresholds
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
    app.state.rule_engine = RuleEngine(
        Thresholds(
            humidity_min=settings.fallback_humidity_min,
            humidity_max=settings.fallback_humidity_max,
            temp_min=settings.fallback_temp_min,
            temp_max=settings.fallback_temp_max,
        )
    )

    try:
        await app.state.event_bus.connect()
        await start_consumer(app)
    except Exception:
        logger.exception("event bus connect failed; alerts won't trigger")

    yield

    try:
        await app.state.event_bus.close()
    finally:
        await app.state.database.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Terramind — Alert Service",
        description="Motor de regras + alertas consumidos do barramento.",
        version="0.1.0",
        docs_url="/alert/docs",
        openapi_url="/alert/openapi.json",
        redoc_url=None,
        lifespan=lifespan,
    )
    apply_standard_middleware(app, settings.cors_allowed_origins)
    app.include_router(alert_router)

    @app.get("/alert/health", tags=["health"], summary="Liveness probe")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": settings.service_name}

    return app


app = create_app()
