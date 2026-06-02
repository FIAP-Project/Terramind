"""DTOs Pydantic do alert-service."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    plot_id: UUID
    sensor_id: UUID
    severity: Severity
    rule_id: str
    message: str
    triggered_at: datetime
    resolved_at: datetime | None = None
