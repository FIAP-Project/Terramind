"""Endpoints CRUD de Crop (cultura). Catálogo global — somente admin gerencia."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from farm_service.dependencies import get_crop_service
from farm_service.schemas import CropCreate, CropOut, CropUpdate
from farm_service.services import CropService
from farm_service.services.crop_service import CropNotFoundError
from terramind_shared.security import Principal, Role, get_current_principal, require_role

router = APIRouter(prefix="/farm/crops", tags=["crops"])


@router.get("", response_model=list[CropOut], summary="Lista culturas do catálogo")
async def list_crops(
    _: Principal = Depends(get_current_principal),
    svc: CropService = Depends(get_crop_service),
) -> list[CropOut]:
    crops = await svc.list_all()
    return [CropOut.model_validate(c) for c in crops]


@router.post(
    "",
    response_model=CropOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma cultura (admin)",
)
async def create_crop(
    payload: CropCreate,
    _: Principal = Depends(require_role(Role.ADMIN)),
    svc: CropService = Depends(get_crop_service),
) -> CropOut:
    crop = await svc.create(payload.model_dump())
    return CropOut.model_validate(crop)


@router.get("/{crop_id}", response_model=CropOut)
async def get_crop(
    crop_id: UUID,
    _: Principal = Depends(get_current_principal),
    svc: CropService = Depends(get_crop_service),
) -> CropOut:
    try:
        crop = await svc.get(crop_id)
    except CropNotFoundError as exc:
        raise HTTPException(status_code=404, detail="crop not found") from exc
    return CropOut.model_validate(crop)


@router.put("/{crop_id}", response_model=CropOut)
async def update_crop(
    crop_id: UUID,
    payload: CropUpdate,
    _: Principal = Depends(require_role(Role.ADMIN)),
    svc: CropService = Depends(get_crop_service),
) -> CropOut:
    try:
        crop = await svc.update(crop_id=crop_id, data=payload.model_dump(exclude_unset=True))
    except CropNotFoundError as exc:
        raise HTTPException(status_code=404, detail="crop not found") from exc
    return CropOut.model_validate(crop)


@router.delete("/{crop_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_crop(
    crop_id: UUID,
    _: Principal = Depends(require_role(Role.ADMIN)),
    svc: CropService = Depends(get_crop_service),
) -> None:
    try:
        await svc.delete(crop_id)
    except CropNotFoundError as exc:
        raise HTTPException(status_code=404, detail="crop not found") from exc
