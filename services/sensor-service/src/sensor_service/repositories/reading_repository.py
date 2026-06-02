"""Persistência de Reading."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sensor_service.models.reading import Reading


class ReadingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, sensor_id: UUID, value: float, unit: str, captured_at: datetime) -> Reading:
        reading = Reading(sensor_id=sensor_id, value=value, unit=unit, captured_at=captured_at)
        self._session.add(reading)
        await self._session.flush()
        return reading

    async def list_for_sensor(
        self,
        sensor_id: UUID,
        *,
        since: datetime | None = None,
        limit: int = 200,
    ) -> list[Reading]:
        stmt = select(Reading).where(Reading.sensor_id == sensor_id)
        if since is not None:
            stmt = stmt.where(Reading.captured_at >= since)
        stmt = stmt.order_by(Reading.captured_at.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
