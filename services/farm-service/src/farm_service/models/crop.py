"""Cultura (ex: milho, soja, café) com faixas ótimas para alertas."""

from __future__ import annotations

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from terramind_shared.db import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Crop(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "crops"
    __table_args__ = {"schema": "farm"}

    name: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    optimal_humidity_min: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    optimal_humidity_max: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    optimal_temp_min: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    optimal_temp_max: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
