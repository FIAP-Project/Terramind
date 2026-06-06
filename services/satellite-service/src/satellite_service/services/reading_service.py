"""Regras de negócio para Reading — persiste e publica evento."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from terramind_shared.events import EventBus, EventType
from terramind_shared.events.schemas import SatelliteReadingRecordedEvent

from satellite_service.models.reading import Reading
from satellite_service.repositories import ReadingRepository, SatelliteRepository
from satellite_service.services.satellite_service import SatelliteNotFoundError


class ReadingService:
    def __init__(
        self,
        *,
        readings: ReadingRepository,
        satellites: SatelliteRepository,
        event_bus: EventBus,
    ) -> None:
        self._readings = readings
        self._satellites = satellites
        self._events = event_bus

    async def record(
        self,
        *,
        satellite_id: UUID,
        value: float,
        unit: str,
        captured_at: datetime,
    ) -> Reading:
        satellite = await self._satellites.get(satellite_id)
        if satellite is None:
            raise SatelliteNotFoundError(str(satellite_id))

        reading = await self._readings.create(
            satellite_id=satellite_id, value=value, unit=unit, captured_at=captured_at
        )

        await self._events.publish(
            EventType.SATELLITE_READING_RECORDED.value,
            SatelliteReadingRecordedEvent(
                satellite_id=str(satellite.id),
                plot_id=str(satellite.plot_id),
                satellite_type=satellite.type,
                value=float(reading.value),
                unit=reading.unit,
                captured_at=reading.captured_at,
            ).model_dump(mode="json"),
        )
        return reading

    async def list_for_satellite(
        self,
        satellite_id: UUID,
        *,
        since: datetime | None = None,
        limit: int = 200,
    ) -> list[Reading]:
        return await self._readings.list_for_satellite(satellite_id, since=since, limit=limit)
