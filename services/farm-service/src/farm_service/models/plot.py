"""Talhão (área dentro de uma fazenda com uma cultura)."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from terramind_shared.db import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Plot(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "plots"
    __table_args__ = {"schema": "farm"}

    farm_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("farm.farms.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    crop_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("farm.crops.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    area_ha: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    planted_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    expected_harvest_at: Mapped[date | None] = mapped_column(Date, nullable=True)
