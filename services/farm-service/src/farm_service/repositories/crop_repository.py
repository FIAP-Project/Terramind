"""Persistência de Crop (cultura)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from farm_service.models.crop import Crop


class CropRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, crop_id: UUID) -> Crop | None:
        return await self._session.get(Crop, crop_id)

    async def get_by_name(self, name: str) -> Crop | None:
        result = await self._session.execute(select(Crop).where(Crop.name == name))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Crop]:
        result = await self._session.execute(select(Crop).order_by(Crop.name))
        return list(result.scalars().all())

    async def create(self, data: dict) -> Crop:
        crop = Crop(**data)
        self._session.add(crop)
        await self._session.flush()
        return crop

    async def update(self, crop: Crop, data: dict) -> Crop:
        for k, v in data.items():
            setattr(crop, k, v)
        await self._session.flush()
        return crop

    async def delete(self, crop: Crop) -> None:
        await self._session.delete(crop)
