"""Persistência de Sensor."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sensor_service.models.sensor import Sensor


class SensorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, sensor_id: UUID) -> Sensor | None:
        return await self._session.get(Sensor, sensor_id)

    async def list_for_plot(self, plot_id: UUID) -> list[Sensor]:
        result = await self._session.execute(
            select(Sensor).where(Sensor.plot_id == plot_id).order_by(Sensor.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_all(self, *, limit: int = 100, offset: int = 0) -> list[Sensor]:
        result = await self._session.execute(
            select(Sensor).order_by(Sensor.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def create(self, data: dict) -> Sensor:
        sensor = Sensor(**data)
        self._session.add(sensor)
        await self._session.flush()
        return sensor

    async def update(self, sensor: Sensor, data: dict) -> Sensor:
        for k, v in data.items():
            setattr(sensor, k, v)
        await self._session.flush()
        return sensor

    async def delete(self, sensor: Sensor) -> None:
        await self._session.delete(sensor)
