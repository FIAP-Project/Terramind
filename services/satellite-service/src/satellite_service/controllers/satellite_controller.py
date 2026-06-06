"""Endpoints CRUD de Satellite."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from terramind_shared.security import Principal, get_current_principal

from satellite_service.dependencies import get_satellite_service
from satellite_service.schemas import SatelliteCreate, SatelliteOut, SatelliteUpdate
from satellite_service.services import SatelliteNotFoundError, SatelliteService

router = APIRouter(prefix="/satellite/satellites", tags=["satellites"])


@router.get(
    "",
    response_model=list[SatelliteOut],
    summary="Lista satélites (opcionalmente filtra por talhão)",
)
async def list_satellites(
    plot_id: UUID | None = Query(default=None),
    _: Principal = Depends(get_current_principal),
    svc: SatelliteService = Depends(get_satellite_service),
) -> list[SatelliteOut]:
    satellites = (
        await svc.list_for_plot(plot_id) if plot_id is not None else await svc.list_all()
    )
    return [SatelliteOut.model_validate(s) for s in satellites]


@router.post(
    "",
    response_model=SatelliteOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registra um novo satélite",
)
async def create_satellite(
    payload: SatelliteCreate,
    _: Principal = Depends(get_current_principal),
    svc: SatelliteService = Depends(get_satellite_service),
) -> SatelliteOut:
    satellite = await svc.create(payload.model_dump(mode="json"))
    return SatelliteOut.model_validate(satellite)


@router.get("/{satellite_id}", response_model=SatelliteOut)
async def get_satellite(
    satellite_id: UUID,
    _: Principal = Depends(get_current_principal),
    svc: SatelliteService = Depends(get_satellite_service),
) -> SatelliteOut:
    try:
        satellite = await svc.get(satellite_id)
    except SatelliteNotFoundError as exc:
        raise HTTPException(status_code=404, detail="satellite not found") from exc
    return SatelliteOut.model_validate(satellite)


@router.put("/{satellite_id}", response_model=SatelliteOut)
async def update_satellite(
    satellite_id: UUID,
    payload: SatelliteUpdate,
    _: Principal = Depends(get_current_principal),
    svc: SatelliteService = Depends(get_satellite_service),
) -> SatelliteOut:
    try:
        satellite = await svc.update(
            satellite_id=satellite_id, data=payload.model_dump(mode="json", exclude_unset=True)
        )
    except SatelliteNotFoundError as exc:
        raise HTTPException(status_code=404, detail="satellite not found") from exc
    return SatelliteOut.model_validate(satellite)


@router.delete("/{satellite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_satellite(
    satellite_id: UUID,
    _: Principal = Depends(get_current_principal),
    svc: SatelliteService = Depends(get_satellite_service),
) -> None:
    try:
        await svc.delete(satellite_id)
    except SatelliteNotFoundError as exc:
        raise HTTPException(status_code=404, detail="satellite not found") from exc
