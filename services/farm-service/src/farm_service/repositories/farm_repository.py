"""Persistência de Farm."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from farm_service.models.farm import Farm


class FarmRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, farm_id: UUID) -> Farm | None:
        return await self._session.get(Farm, farm_id)

    async def list_for_owner(
        self, owner_user_id: UUID, *, limit: int = 100, offset: int = 0
    ) -> list[Farm]:
        result = await self._session.execute(
            select(Farm)
            .where(Farm.owner_user_id == owner_user_id)
            .order_by(Farm.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def create(self, *, owner_user_id: UUID, data: dict) -> Farm:
        farm = Farm(owner_user_id=owner_user_id, **data)
        self._session.add(farm)
        await self._session.flush()
        return farm

    async def update(self, farm: Farm, data: dict) -> Farm:
        for k, v in data.items():
            setattr(farm, k, v)
        await self._session.flush()
        return farm

    async def delete(self, farm: Farm) -> None:
        await self._session.delete(farm)
