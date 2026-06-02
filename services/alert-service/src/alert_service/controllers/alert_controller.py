"""Endpoints HTTP de Alert."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from alert_service.dependencies import get_alert_service
from alert_service.schemas import AlertOut, Severity
from alert_service.services import AlertNotFoundError, AlertService
from terramind_shared.security import Principal, Role, get_current_principal, require_role

router = APIRouter(prefix="/alert/alerts", tags=["alerts"])


@router.get(
    "",
    response_model=list[AlertOut],
    summary="Lista alertas (filtros: plot_id, severity, resolved)",
)
async def list_alerts(
    plot_id: UUID | None = Query(default=None),
    severity: Severity | None = Query(default=None),
    resolved: bool | None = Query(default=None),
    _: Principal = Depends(get_current_principal),
    svc: AlertService = Depends(get_alert_service),
) -> list[AlertOut]:
    alerts = await svc.list(
        plot_id=plot_id,
        severity=severity.value if severity else None,
        resolved=resolved,
    )
    return [AlertOut.model_validate(a) for a in alerts]


@router.get("/{alert_id}", response_model=AlertOut, summary="Retorna um alerta")
async def get_alert(
    alert_id: UUID,
    _: Principal = Depends(get_current_principal),
    svc: AlertService = Depends(get_alert_service),
) -> AlertOut:
    try:
        alert = await svc.get(alert_id)
    except AlertNotFoundError as exc:
        raise HTTPException(status_code=404, detail="alert not found") from exc
    return AlertOut.model_validate(alert)


@router.patch(
    "/{alert_id}/resolve",
    response_model=AlertOut,
    summary="Marca um alerta como resolvido (agronomist+)",
)
async def resolve_alert(
    alert_id: UUID,
    _: Principal = Depends(require_role(Role.AGRONOMIST)),
    svc: AlertService = Depends(get_alert_service),
) -> AlertOut:
    try:
        alert = await svc.resolve(alert_id)
    except AlertNotFoundError as exc:
        raise HTTPException(status_code=404, detail="alert not found") from exc
    return AlertOut.model_validate(alert)
