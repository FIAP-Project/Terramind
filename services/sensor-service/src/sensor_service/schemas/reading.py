"""DTOs de Reading."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReadingCreate(BaseModel):
    value: float = Field(..., ge=-1e9, le=1e9)
    unit: str = Field(..., min_length=1, max_length=16)
    captured_at: datetime


class ReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sensor_id: UUID
    value: float
    unit: str
    captured_at: datetime
    ingested_at: datetime
