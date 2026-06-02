"""Regras de negócio para Farm."""

from __future__ import annotations

from uuid import UUID

from farm_service.models.farm import Farm
from farm_service.repositories import FarmRepository


class FarmNotFoundError(Exception):
    pass


class ForbiddenFarmError(Exception):
    """O usuário autenticado não é dono da fazenda."""


class FarmService:
    def __init__(self, farms: FarmRepository) -> None:
        self._farms = farms

    async def list_for_owner(self, owner_user_id: UUID) -> list[Farm]:
        return await self._farms.list_for_owner(owner_user_id)

    async def get_owned(self, farm_id: UUID, owner_user_id: UUID) -> Farm:
        farm = await self._farms.get(farm_id)
        if farm is None:
            raise FarmNotFoundError(str(farm_id))
        if farm.owner_user_id != owner_user_id:
            raise ForbiddenFarmError(str(farm_id))
        return farm

    async def create(self, *, owner_user_id: UUID, data: dict) -> Farm:
        return await self._farms.create(owner_user_id=owner_user_id, data=data)

    async def update(self, *, farm_id: UUID, owner_user_id: UUID, data: dict) -> Farm:
        farm = await self.get_owned(farm_id, owner_user_id)
        return await self._farms.update(farm, data)

    async def delete(self, *, farm_id: UUID, owner_user_id: UUID) -> None:
        farm = await self.get_owned(farm_id, owner_user_id)
        await self._farms.delete(farm)
