"""Regras de negócio para CRUD/list de Alerts e processamento de eventos."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from alert_service.models.alert import Alert
from alert_service.repositories import AlertRepository
from alert_service.services.rule_engine import RuleEngine
from terramind_shared.events import EventBus, EventType
from terramind_shared.events.schemas import AlertResolvedEvent, AlertTriggeredEvent


class AlertNotFoundError(Exception):
    pass


class AlertService:
    def __init__(
        self,
        *,
        alerts: AlertRepository,
        rule_engine: RuleEngine,
        event_bus: EventBus,
    ) -> None:
        self._alerts = alerts
        self._engine = rule_engine
        self._events = event_bus

    async def list(
        self,
        *,
        plot_id: UUID | None = None,
        severity: str | None = None,
        resolved: bool | None = None,
    ) -> list[Alert]:
        return await self._alerts.list(plot_id=plot_id, severity=severity, resolved=resolved)

    async def get(self, alert_id: UUID) -> Alert:
        alert = await self._alerts.get(alert_id)
        if alert is None:
            raise AlertNotFoundError(str(alert_id))
        return alert

    async def resolve(self, alert_id: UUID) -> Alert:
        alert = await self.get(alert_id)
        if alert.resolved_at is not None:
            return alert
        alert = await self._alerts.resolve(alert)
        await self._events.publish(
            EventType.ALERT_RESOLVED.value,
            AlertResolvedEvent(
                alert_id=str(alert.id), plot_id=str(alert.plot_id)
            ).model_dump(mode="json"),
        )
        return alert

    async def process_reading(
        self,
        *,
        plot_id: UUID,
        satellite_id: UUID,
        satellite_type: str,
        value: float,
        unit: str,
        captured_at: datetime,
    ) -> Alert | None:
        """Avalia uma leitura. Se a regra dispara, cria Alert e publica evento."""
        result = self._engine.evaluate(satellite_type=satellite_type, value=value, unit=unit)
        if not result.triggered:
            return None
        alert = await self._alerts.create(
            plot_id=plot_id,
            satellite_id=satellite_id,
            severity=result.severity,
            rule_id=result.rule_id,
            message=result.message,
            triggered_at=captured_at,
        )
        await self._events.publish(
            EventType.ALERT_TRIGGERED.value,
            AlertTriggeredEvent(
                alert_id=str(alert.id),
                plot_id=str(alert.plot_id),
                severity=alert.severity,
                message=alert.message,
            ).model_dump(mode="json"),
        )
        return alert
