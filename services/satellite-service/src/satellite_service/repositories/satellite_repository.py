"""Persistência de Satellite."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from satellite_service.models.satellite import Satellite


class SatelliteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, satellite_id: UUID) -> Satellite | None:
        return await self._session.get(Satellite, satellite_id)

    async def list_for_plot(self, plot_id: UUID) -> list[Satellite]:
        result = await self._session.execute(
            select(Satellite)
            .where(Satellite.plot_id == plot_id)
            .order_by(Satellite.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_all(self, *, limit: int = 100, offset: int = 0) -> list[Satellite]:
        result = await self._session.execute(
            select(Satellite).order_by(Satellite.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def create(self, data: dict) -> Satellite:
        satellite = Satellite(**data)
        self._session.add(satellite)
        await self._session.flush()
        return satellite

    async def update(self, satellite: Satellite, data: dict) -> Satellite:
        for k, v in data.items():
            setattr(satellite, k, v)
        await self._session.flush()
        return satellite

    async def delete(self, satellite: Satellite) -> None:
        await self._session.delete(satellite)
