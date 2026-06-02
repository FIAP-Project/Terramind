"""Regras de negócio para Crop (cultura)."""

from __future__ import annotations

from uuid import UUID

from farm_service.models.crop import Crop
from farm_service.repositories import CropRepository


class CropNotFoundError(Exception):
    pass


class CropService:
    def __init__(self, crops: CropRepository) -> None:
        self._crops = crops

    async def list_all(self) -> list[Crop]:
        return await self._crops.list_all()

    async def get(self, crop_id: UUID) -> Crop:
        crop = await self._crops.get(crop_id)
        if crop is None:
            raise CropNotFoundError(str(crop_id))
        return crop

    async def create(self, data: dict) -> Crop:
        return await self._crops.create(data)

    async def update(self, *, crop_id: UUID, data: dict) -> Crop:
        crop = await self.get(crop_id)
        return await self._crops.update(crop, data)

    async def delete(self, crop_id: UUID) -> None:
        crop = await self.get(crop_id)
        await self._crops.delete(crop)
