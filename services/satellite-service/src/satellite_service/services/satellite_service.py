"""Regras de negócio para Satellite."""

from __future__ import annotations

from uuid import UUID

from satellite_service.models.satellite import Satellite
from satellite_service.repositories import SatelliteRepository


class SatelliteNotFoundError(Exception):
    pass


class SatelliteService:
    def __init__(self, satellites: SatelliteRepository) -> None:
        self._satellites = satellites

    async def list_all(self) -> list[Satellite]:
        return await self._satellites.list_all()

    async def list_for_plot(self, plot_id: UUID) -> list[Satellite]:
        return await self._satellites.list_for_plot(plot_id)

    async def get(self, satellite_id: UUID) -> Satellite:
        satellite = await self._satellites.get(satellite_id)
        if satellite is None:
            raise SatelliteNotFoundError(str(satellite_id))
        return satellite

    async def create(self, data: dict) -> Satellite:
        return await self._satellites.create(data)

    async def update(self, *, satellite_id: UUID, data: dict) -> Satellite:
        satellite = await self.get(satellite_id)
        return await self._satellites.update(satellite, data)

    async def delete(self, satellite_id: UUID) -> None:
        satellite = await self.get(satellite_id)
        await self._satellites.delete(satellite)
