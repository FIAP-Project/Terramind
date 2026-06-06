"""Persistência de Alert."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from alert_service.models.alert import Alert


class AlertRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, alert_id: UUID) -> Alert | None:
        return await self._session.get(Alert, alert_id)

    async def list(
        self,
        *,
        plot_id: UUID | None = None,
        severity: str | None = None,
        resolved: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Alert]:
        stmt = select(Alert)
        if plot_id is not None:
            stmt = stmt.where(Alert.plot_id == plot_id)
        if severity is not None:
            stmt = stmt.where(Alert.severity == severity)
        if resolved is True:
            stmt = stmt.where(Alert.resolved_at.is_not(None))
        elif resolved is False:
            stmt = stmt.where(Alert.resolved_at.is_(None))
        stmt = stmt.order_by(Alert.triggered_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        *,
        plot_id: UUID,
        satellite_id: UUID,
        severity: str,
        rule_id: str,
        message: str,
        triggered_at: datetime,
    ) -> Alert:
        alert = Alert(
            plot_id=plot_id,
            satellite_id=satellite_id,
            severity=severity,
            rule_id=rule_id,
            message=message,
            triggered_at=triggered_at,
        )
        self._session.add(alert)
        await self._session.flush()
        return alert

    async def resolve(self, alert: Alert) -> Alert:
        alert.resolved_at = datetime.now(UTC)
        await self._session.flush()
        return alert
