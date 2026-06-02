"""Regras de negócio para Plot."""

from __future__ import annotations

from uuid import UUID

from farm_service.models.plot import Plot
from farm_service.repositories import FarmRepository, PlotRepository
from farm_service.services.farm_service import ForbiddenFarmError


class PlotNotFoundError(Exception):
    pass


class PlotService:
    def __init__(self, plots: PlotRepository, farms: FarmRepository) -> None:
        self._plots = plots
        self._farms = farms

    async def list_for_farm(self, *, farm_id: UUID, owner_user_id: UUID) -> list[Plot]:
        await self._assert_owner(farm_id, owner_user_id)
        return await self._plots.list_for_farm(farm_id)

    async def get_owned(self, plot_id: UUID, owner_user_id: UUID) -> Plot:
        plot = await self._plots.get(plot_id)
        if plot is None:
            raise PlotNotFoundError(str(plot_id))
        await self._assert_owner(plot.farm_id, owner_user_id)
        return plot

    async def create(self, *, owner_user_id: UUID, data: dict) -> Plot:
        await self._assert_owner(data["farm_id"], owner_user_id)
        return await self._plots.create(data)

    async def update(self, *, plot_id: UUID, owner_user_id: UUID, data: dict) -> Plot:
        plot = await self.get_owned(plot_id, owner_user_id)
        return await self._plots.update(plot, data)

    async def delete(self, *, plot_id: UUID, owner_user_id: UUID) -> None:
        plot = await self.get_owned(plot_id, owner_user_id)
        await self._plots.delete(plot)

    async def _assert_owner(self, farm_id: UUID, owner_user_id: UUID) -> None:
        farm = await self._farms.get(farm_id)
        if farm is None or farm.owner_user_id != owner_user_id:
            raise ForbiddenFarmError(str(farm_id))
