"""Endpoints CRUD de Plot."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from farm_service.dependencies import get_plot_service
from farm_service.schemas import PlotCreate, PlotOut, PlotUpdate
from farm_service.services import PlotNotFoundError, PlotService
from farm_service.services.farm_service import ForbiddenFarmError
from terramind_shared.security import Principal, get_current_principal

router = APIRouter(prefix="/farm/plots", tags=["plots"])


@router.get("", response_model=list[PlotOut], summary="Lista talhões de uma fazenda")
async def list_plots(
    farm_id: UUID = Query(...),
    principal: Principal = Depends(get_current_principal),
    svc: PlotService = Depends(get_plot_service),
) -> list[PlotOut]:
    try:
        plots = await svc.list_for_farm(farm_id=farm_id, owner_user_id=UUID(principal.user_id))
    except ForbiddenFarmError as exc:
        raise HTTPException(status_code=403, detail="not your farm") from exc
    return [PlotOut.model_validate(p) for p in plots]


@router.post("", response_model=PlotOut, status_code=status.HTTP_201_CREATED)
async def create_plot(
    payload: PlotCreate,
    principal: Principal = Depends(get_current_principal),
    svc: PlotService = Depends(get_plot_service),
) -> PlotOut:
    try:
        plot = await svc.create(
            owner_user_id=UUID(principal.user_id), data=payload.model_dump()
        )
    except ForbiddenFarmError as exc:
        raise HTTPException(status_code=403, detail="not your farm") from exc
    return PlotOut.model_validate(plot)


@router.get("/{plot_id}", response_model=PlotOut)
async def get_plot(
    plot_id: UUID,
    principal: Principal = Depends(get_current_principal),
    svc: PlotService = Depends(get_plot_service),
) -> PlotOut:
    try:
        plot = await svc.get_owned(plot_id, UUID(principal.user_id))
    except PlotNotFoundError as exc:
        raise HTTPException(status_code=404, detail="plot not found") from exc
    except ForbiddenFarmError as exc:
        raise HTTPException(status_code=403, detail="not your farm") from exc
    return PlotOut.model_validate(plot)


@router.put("/{plot_id}", response_model=PlotOut)
async def update_plot(
    plot_id: UUID,
    payload: PlotUpdate,
    principal: Principal = Depends(get_current_principal),
    svc: PlotService = Depends(get_plot_service),
) -> PlotOut:
    try:
        plot = await svc.update(
            plot_id=plot_id,
            owner_user_id=UUID(principal.user_id),
            data=payload.model_dump(exclude_unset=True),
        )
    except PlotNotFoundError as exc:
        raise HTTPException(status_code=404, detail="plot not found") from exc
    except ForbiddenFarmError as exc:
        raise HTTPException(status_code=403, detail="not your farm") from exc
    return PlotOut.model_validate(plot)


@router.delete("/{plot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plot(
    plot_id: UUID,
    principal: Principal = Depends(get_current_principal),
    svc: PlotService = Depends(get_plot_service),
) -> None:
    try:
        await svc.delete(plot_id=plot_id, owner_user_id=UUID(principal.user_id))
    except PlotNotFoundError as exc:
        raise HTTPException(status_code=404, detail="plot not found") from exc
    except ForbiddenFarmError as exc:
        raise HTTPException(status_code=403, detail="not your farm") from exc
