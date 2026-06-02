"""DI do farm-service."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from farm_service.repositories import CropRepository, FarmRepository, PlotRepository
from farm_service.services import CropService, FarmService, PlotService


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    db = request.app.state.database
    async for session in db.session():
        yield session


def get_farm_service(session: AsyncSession = Depends(get_db_session)) -> FarmService:
    return FarmService(FarmRepository(session))


def get_plot_service(session: AsyncSession = Depends(get_db_session)) -> PlotService:
    return PlotService(PlotRepository(session), FarmRepository(session))


def get_crop_service(session: AsyncSession = Depends(get_db_session)) -> CropService:
    return CropService(CropRepository(session))
