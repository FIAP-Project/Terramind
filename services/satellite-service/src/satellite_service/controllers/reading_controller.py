"""Endpoints de Readings (ingestão e consulta)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from terramind_shared.security import Principal, get_current_principal

from satellite_service.dependencies import get_reading_service
from satellite_service.schemas import ReadingCreate, ReadingOut
from satellite_service.services import ReadingService, SatelliteNotFoundError

router = APIRouter(prefix="/satellite/satellites", tags=["readings"])


@router.post(
    "/{satellite_id}/readings",
    response_model=ReadingOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registra uma leitura do satélite (gera evento)",
)
async def post_reading(
    satellite_id: UUID,
    payload: ReadingCreate,
    _: Principal = Depends(get_current_principal),
    svc: ReadingService = Depends(get_reading_service),
) -> ReadingOut:
    try:
        reading = await svc.record(
            satellite_id=satellite_id,
            value=payload.value,
            unit=payload.unit,
            captured_at=payload.captured_at,
        )
    except SatelliteNotFoundError as exc:
        raise HTTPException(status_code=404, detail="satellite not found") from exc
    return ReadingOut.model_validate(reading)


@router.get(
    "/{satellite_id}/readings",
    response_model=list[ReadingOut],
    summary="Lista as últimas leituras de um satélite",
)
async def list_readings(
    satellite_id: UUID,
    since: datetime | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    _: Principal = Depends(get_current_principal),
    svc: ReadingService = Depends(get_reading_service),
) -> list[ReadingOut]:
    readings = await svc.list_for_satellite(satellite_id, since=since, limit=limit)
    return [ReadingOut.model_validate(r) for r in readings]
