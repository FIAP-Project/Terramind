"""Endpoints CRUD de Sensor."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from sensor_service.dependencies import get_sensor_service
from sensor_service.schemas import SensorCreate, SensorOut, SensorUpdate
from sensor_service.services import SensorNotFoundError, SensorService
from terramind_shared.security import Principal, get_current_principal

router = APIRouter(prefix="/sensor/sensors", tags=["sensors"])


@router.get("", response_model=list[SensorOut], summary="Lista sensores (opcionalmente filtra por talhão)")
async def list_sensors(
    plot_id: UUID | None = Query(default=None),
    _: Principal = Depends(get_current_principal),
    svc: SensorService = Depends(get_sensor_service),
) -> list[SensorOut]:
    sensors = (
        await svc.list_for_plot(plot_id) if plot_id is not None else await svc.list_all()
    )
    return [SensorOut.model_validate(s) for s in sensors]


@router.post(
    "",
    response_model=SensorOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registra um novo sensor",
)
async def create_sensor(
    payload: SensorCreate,
    _: Principal = Depends(get_current_principal),
    svc: SensorService = Depends(get_sensor_service),
) -> SensorOut:
    sensor = await svc.create(payload.model_dump(mode="json"))
    return SensorOut.model_validate(sensor)


@router.get("/{sensor_id}", response_model=SensorOut)
async def get_sensor(
    sensor_id: UUID,
    _: Principal = Depends(get_current_principal),
    svc: SensorService = Depends(get_sensor_service),
) -> SensorOut:
    try:
        sensor = await svc.get(sensor_id)
    except SensorNotFoundError as exc:
        raise HTTPException(status_code=404, detail="sensor not found") from exc
    return SensorOut.model_validate(sensor)


@router.put("/{sensor_id}", response_model=SensorOut)
async def update_sensor(
    sensor_id: UUID,
    payload: SensorUpdate,
    _: Principal = Depends(get_current_principal),
    svc: SensorService = Depends(get_sensor_service),
) -> SensorOut:
    try:
        sensor = await svc.update(
            sensor_id=sensor_id, data=payload.model_dump(mode="json", exclude_unset=True)
        )
    except SensorNotFoundError as exc:
        raise HTTPException(status_code=404, detail="sensor not found") from exc
    return SensorOut.model_validate(sensor)


@router.delete("/{sensor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sensor(
    sensor_id: UUID,
    _: Principal = Depends(get_current_principal),
    svc: SensorService = Depends(get_sensor_service),
) -> None:
    try:
        await svc.delete(sensor_id)
    except SensorNotFoundError as exc:
        raise HTTPException(status_code=404, detail="sensor not found") from exc
