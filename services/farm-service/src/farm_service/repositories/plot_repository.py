"""Persistência de Plot (talhão)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from farm_service.models.plot import Plot


class PlotRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, plot_id: UUID) -> Plot | None:
        return await self._session.get(Plot, plot_id)

    async def list_for_farm(self, farm_id: UUID) -> list[Plot]:
        result = await self._session.execute(
            select(Plot).where(Plot.farm_id == farm_id).order_by(Plot.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, data: dict) -> Plot:
        plot = Plot(**data)
        self._session.add(plot)
        await self._session.flush()
        return plot

    async def update(self, plot: Plot, data: dict) -> Plot:
        for k, v in data.items():
            setattr(plot, k, v)
        await self._session.flush()
        return plot

    async def delete(self, plot: Plot) -> None:
        await self._session.delete(plot)
