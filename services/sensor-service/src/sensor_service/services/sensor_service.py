"""Regras de negócio para Sensor."""

from __future__ import annotations

from uuid import UUID

from sensor_service.models.sensor import Sensor
from sensor_service.repositories import SensorRepository


class SensorNotFoundError(Exception):
    pass


class SensorService:
    def __init__(self, sensors: SensorRepository) -> None:
        self._sensors = sensors

    async def list_all(self) -> list[Sensor]:
        return await self._sensors.list_all()

    async def list_for_plot(self, plot_id: UUID) -> list[Sensor]:
        return await self._sensors.list_for_plot(plot_id)

    async def get(self, sensor_id: UUID) -> Sensor:
        sensor = await self._sensors.get(sensor_id)
        if sensor is None:
            raise SensorNotFoundError(str(sensor_id))
        return sensor

    async def create(self, data: dict) -> Sensor:
        return await self._sensors.create(data)

    async def update(self, *, sensor_id: UUID, data: dict) -> Sensor:
        sensor = await self.get(sensor_id)
        return await self._sensors.update(sensor, data)

    async def delete(self, sensor_id: UUID) -> None:
        sensor = await self.get(sensor_id)
        await self._sensors.delete(sensor)
