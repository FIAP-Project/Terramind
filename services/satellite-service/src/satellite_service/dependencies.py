"""DI do satellite-service."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from satellite_service.repositories import ReadingRepository, SatelliteRepository
from satellite_service.services import ReadingService, SatelliteService


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    db = request.app.state.database
    async for session in db.session():
        yield session


def get_satellite_service(session: AsyncSession = Depends(get_db_session)) -> SatelliteService:
    return SatelliteService(SatelliteRepository(session))


def get_reading_service(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> ReadingService:
    return ReadingService(
        readings=ReadingRepository(session),
        satellites=SatelliteRepository(session),
        event_bus=request.app.state.event_bus,
    )
