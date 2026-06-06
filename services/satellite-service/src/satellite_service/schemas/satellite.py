"""DTOs de Satellite."""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SatelliteType(StrEnum):
    SOIL_MOISTURE = "soil_moisture"
    TEMPERATURE = "temperature"
    RAINFALL = "rainfall"
    NPK = "npk"


class SatelliteStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


class SatelliteBase(BaseModel):
    plot_id: UUID
    type: SatelliteType
    serial_number: str = Field(..., min_length=1, max_length=80)
    status: SatelliteStatus = SatelliteStatus.ACTIVE
    description: str | None = Field(default=None, max_length=255)


class SatelliteCreate(SatelliteBase):
    pass


class SatelliteUpdate(BaseModel):
    type: SatelliteType | None = None
    status: SatelliteStatus | None = None
    description: str | None = Field(default=None, max_length=255)


class SatelliteOut(SatelliteBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
