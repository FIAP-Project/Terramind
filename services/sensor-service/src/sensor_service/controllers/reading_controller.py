"""Endpoints de Readings (ingestão e consulta)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from sensor_service.dependencies import get_reading_service
from sensor_service.schemas import ReadingCreate, ReadingOut
from sensor_service.services import ReadingService, SensorNotFoundError
from terramind_shared.security import Principal, get_current_principal

router = APIRouter(prefix="/sensor/sensors", tags=["readings"])


@router.post(
    "/{sensor_id}/readings",
    response_model=ReadingOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registra uma leitura do sensor (gera evento)",
)
async def post_reading(
    sensor_id: UUID,
    payload: ReadingCreate,
    _: Principal = Depends(get_current_principal),
    svc: ReadingService = Depends(get_reading_service),
) -> ReadingOut:
    try:
        reading = await svc.record(
            sensor_id=sensor_id,
            value=payload.value,
            unit=payload.unit,
            captured_at=payload.captured_at,
        )
    except SensorNotFoundError as exc:
        raise HTTPException(status_code=404, detail="sensor not found") from exc
    return ReadingOut.model_validate(reading)


@router.get(
    "/{sensor_id}/readings",
    response_model=list[ReadingOut],
    summary="Lista as últimas leituras de um sensor",
)
async def list_readings(
    sensor_id: UUID,
    since: datetime | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    _: Principal = Depends(get_current_principal),
    svc: ReadingService = Depends(get_reading_service),
) -> list[ReadingOut]:
    readings = await svc.list_for_sensor(sensor_id, since=since, limit=limit)
    return [ReadingOut.model_validate(r) for r in readings]
