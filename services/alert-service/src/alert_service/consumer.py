"""Consumer de eventos `satellite.reading.recorded` que dispara o rule engine."""

from __future__ import annotations

import logging
from uuid import UUID

from alert_service.repositories import AlertRepository
from alert_service.services import AlertService
from terramind_shared.events import EventBus, EventEnvelope, EventType

logger = logging.getLogger(__name__)


def make_handler(database, rule_engine, event_bus: EventBus):  # noqa: ANN001
    """Factory que captura dependências via closure.

    Cada evento abre sua própria sessão, processa e fecha — sem reaproveitar
    a sessão entre eventos.
    """

    async def handle(envelope: EventEnvelope) -> None:
        payload = envelope.payload
        try:
            satellite_id = UUID(payload["satellite_id"])
            plot_id = UUID(payload["plot_id"])
            satellite_type = str(payload["satellite_type"])
            value = float(payload["value"])
            unit = str(payload["unit"])
            from datetime import datetime

            captured_at = datetime.fromisoformat(payload["captured_at"])
        except (KeyError, ValueError, TypeError):
            logger.exception("invalid reading payload: %s", payload)
            return

        async for session in database.session():
            svc = AlertService(
                alerts=AlertRepository(session),
                rule_engine=rule_engine,
                event_bus=event_bus,
            )
            await svc.process_reading(
                plot_id=plot_id,
                satellite_id=satellite_id,
                satellite_type=satellite_type,
                value=value,
                unit=unit,
                captured_at=captured_at,
            )

    return handle


async def start_consumer(app) -> None:  # noqa: ANN001
    bus: EventBus = app.state.event_bus
    handler = make_handler(app.state.database, app.state.rule_engine, bus)
    await bus.subscribe(
        queue_name="alert-service.readings",
        routing_keys=[EventType.SATELLITE_READING_RECORDED.value],
        handler=handler,
    )
    logger.info("alert-service consumer ready")
