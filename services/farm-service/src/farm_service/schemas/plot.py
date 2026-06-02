"""DTOs de Plot (talhão)."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PlotBase(BaseModel):
    farm_id: UUID
    crop_id: UUID | None = None
    name: str = Field(..., min_length=2, max_length=120)
    area_ha: float = Field(..., gt=0)
    planted_at: date | None = None
    expected_harvest_at: date | None = None


class PlotCreate(PlotBase):
    pass


class PlotUpdate(BaseModel):
    crop_id: UUID | None = None
    name: str | None = Field(default=None, min_length=2, max_length=120)
    area_ha: float | None = Field(default=None, gt=0)
    planted_at: date | None = None
    expected_harvest_at: date | None = None


class PlotOut(PlotBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
