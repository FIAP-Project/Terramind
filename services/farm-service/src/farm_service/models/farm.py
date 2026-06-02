"""Fazenda (propriedade rural)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from terramind_shared.db import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Farm(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "farms"
    __table_args__ = {"schema": "farm"}

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    owner_user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), index=True, nullable=False)
    area_ha: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    latitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
