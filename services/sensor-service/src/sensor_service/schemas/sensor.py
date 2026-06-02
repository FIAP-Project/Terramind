"""DTOs de Sensor."""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SensorType(StrEnum):
    SOIL_MOISTURE = "soil_moisture"
    TEMPERATURE = "temperature"
    RAINFALL = "rainfall"
    NPK = "npk"


class SensorStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


class SensorBase(BaseModel):
    plot_id: UUID
    type: SensorType
    serial_number: str = Field(..., min_length=1, max_length=80)
    status: SensorStatus = SensorStatus.ACTIVE
    description: str | None = Field(default=None, max_length=255)


class SensorCreate(SensorBase):
    pass


class SensorUpdate(BaseModel):
    type: SensorType | None = None
    status: SensorStatus | None = None
    description: str | None = Field(default=None, max_length=255)


class SensorOut(SensorBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
