"""Regras de negócio para Reading — persiste e publica evento."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sensor_service.models.reading import Reading
from sensor_service.repositories import ReadingRepository, SensorRepository
from sensor_service.services.sensor_service import SensorNotFoundError
from terramind_shared.events import EventBus, EventType
from terramind_shared.events.schemas import SensorReadingRecordedEvent


class ReadingService:
    def __init__(
        self,
        *,
        readings: ReadingRepository,
        sensors: SensorRepository,
        event_bus: EventBus,
    ) -> None:
        self._readings = readings
        self._sensors = sensors
        self._events = event_bus

    async def record(
        self,
        *,
        sensor_id: UUID,
        value: float,
        unit: str,
        captured_at: datetime,
    ) -> Reading:
        sensor = await self._sensors.get(sensor_id)
        if sensor is None:
            raise SensorNotFoundError(str(sensor_id))

        reading = await self._readings.create(
            sensor_id=sensor_id, value=value, unit=unit, captured_at=captured_at
        )

        await self._events.publish(
            EventType.SENSOR_READING_RECORDED.value,
            SensorReadingRecordedEvent(
                sensor_id=str(sensor.id),
                plot_id=str(sensor.plot_id),
                sensor_type=sensor.type,
                value=float(reading.value),
                unit=reading.unit,
                captured_at=reading.captured_at,
            ).model_dump(mode="json"),
        )
        return reading

    async def list_for_sensor(
        self,
        sensor_id: UUID,
        *,
        since: datetime | None = None,
        limit: int = 200,
    ) -> list[Reading]:
        return await self._readings.list_for_sensor(sensor_id, since=since, limit=limit)
