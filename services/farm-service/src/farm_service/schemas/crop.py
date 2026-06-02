"""DTOs de Crop (cultura)."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CropBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=255)
    optimal_humidity_min: float = Field(..., ge=0, le=100)
    optimal_humidity_max: float = Field(..., ge=0, le=100)
    optimal_temp_min: float = Field(..., ge=-50, le=80)
    optimal_temp_max: float = Field(..., ge=-50, le=80)

    @model_validator(mode="after")
    def _ranges_ok(self) -> "CropBase":
        if self.optimal_humidity_min >= self.optimal_humidity_max:
            raise ValueError("optimal_humidity_min must be < optimal_humidity_max")
        if self.optimal_temp_min >= self.optimal_temp_max:
            raise ValueError("optimal_temp_min must be < optimal_temp_max")
        return self


class CropCreate(CropBase):
    pass


class CropUpdate(BaseModel):
    description: str | None = Field(default=None, max_length=255)
    optimal_humidity_min: float | None = Field(default=None, ge=0, le=100)
    optimal_humidity_max: float | None = Field(default=None, ge=0, le=100)
    optimal_temp_min: float | None = Field(default=None, ge=-50, le=80)
    optimal_temp_max: float | None = Field(default=None, ge=-50, le=80)


class CropOut(CropBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
