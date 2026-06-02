"""Sensor IoT associado a um talhão."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from terramind_shared.db import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Sensor(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sensors"
    __table_args__ = {"schema": "sensor"}

    plot_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), index=True, nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    serial_number: Mapped[str] = mapped_column(
        String(80), unique=True, index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(String(16), default="active", nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
