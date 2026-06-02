"""DI do sensor-service."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from sensor_service.repositories import ReadingRepository, SensorRepository
from sensor_service.services import ReadingService, SensorService


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    db = request.app.state.database
    async for session in db.session():
        yield session


def get_sensor_service(session: AsyncSession = Depends(get_db_session)) -> SensorService:
    return SensorService(SensorRepository(session))


def get_reading_service(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> ReadingService:
    return ReadingService(
        readings=ReadingRepository(session),
        sensors=SensorRepository(session),
        event_bus=request.app.state.event_bus,
    )
