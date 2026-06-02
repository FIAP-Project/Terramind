"""Endpoints CRUD de Farm."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from farm_service.dependencies import get_farm_service
from farm_service.schemas import FarmCreate, FarmOut, FarmUpdate
from farm_service.services import FarmNotFoundError, FarmService, ForbiddenFarmError
from terramind_shared.security import Principal, get_current_principal

router = APIRouter(prefix="/farm/farms", tags=["farms"])


@router.get("", response_model=list[FarmOut], summary="Lista fazendas do usuário")
async def list_farms(
    principal: Principal = Depends(get_current_principal),
    svc: FarmService = Depends(get_farm_service),
) -> list[FarmOut]:
    farms = await svc.list_for_owner(UUID(principal.user_id))
    return [FarmOut.model_validate(f) for f in farms]


@router.post(
    "",
    response_model=FarmOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma fazenda",
)
async def create_farm(
    payload: FarmCreate,
    principal: Principal = Depends(get_current_principal),
    svc: FarmService = Depends(get_farm_service),
) -> FarmOut:
    farm = await svc.create(
        owner_user_id=UUID(principal.user_id),
        data=payload.model_dump(),
    )
    return FarmOut.model_validate(farm)


@router.get("/{farm_id}", response_model=FarmOut, summary="Retorna uma fazenda")
async def get_farm(
    farm_id: UUID,
    principal: Principal = Depends(get_current_principal),
    svc: FarmService = Depends(get_farm_service),
) -> FarmOut:
    try:
        farm = await svc.get_owned(farm_id, UUID(principal.user_id))
    except FarmNotFoundError as exc:
        raise HTTPException(status_code=404, detail="farm not found") from exc
    except ForbiddenFarmError as exc:
        raise HTTPException(status_code=403, detail="not your farm") from exc
    return FarmOut.model_validate(farm)


@router.put("/{farm_id}", response_model=FarmOut, summary="Atualiza uma fazenda")
async def update_farm(
    farm_id: UUID,
    payload: FarmUpdate,
    principal: Principal = Depends(get_current_principal),
    svc: FarmService = Depends(get_farm_service),
) -> FarmOut:
    try:
        farm = await svc.update(
            farm_id=farm_id,
            owner_user_id=UUID(principal.user_id),
            data=payload.model_dump(exclude_unset=True),
        )
    except FarmNotFoundError as exc:
        raise HTTPException(status_code=404, detail="farm not found") from exc
    except ForbiddenFarmError as exc:
        raise HTTPException(status_code=403, detail="not your farm") from exc
    return FarmOut.model_validate(farm)


@router.delete(
    "/{farm_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove uma fazenda",
)
async def delete_farm(
    farm_id: UUID,
    principal: Principal = Depends(get_current_principal),
    svc: FarmService = Depends(get_farm_service),
) -> None:
    try:
        await svc.delete(farm_id=farm_id, owner_user_id=UUID(principal.user_id))
    except FarmNotFoundError as exc:
        raise HTTPException(status_code=404, detail="farm not found") from exc
    except ForbiddenFarmError as exc:
        raise HTTPException(status_code=403, detail="not your farm") from exc
