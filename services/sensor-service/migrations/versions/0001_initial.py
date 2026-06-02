"""initial sensor schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-01

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS sensor")

    op.create_table(
        "sensors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("plot_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("serial_number", sa.String(length=80), nullable=False, unique=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="active"),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="sensor",
    )
    op.create_index("ix_sensors_plot_id", "sensors", ["plot_id"], schema="sensor")
    op.create_index("ix_sensors_serial_number", "sensors", ["serial_number"], unique=True, schema="sensor")

    op.create_table(
        "readings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("sensor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("value", sa.Numeric(12, 4), nullable=False),
        sa.Column("unit", sa.String(length=16), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["sensor_id"], ["sensor.sensors.id"], ondelete="CASCADE"),
        schema="sensor",
    )
    op.create_index("ix_readings_sensor_id", "readings", ["sensor_id"], schema="sensor")
    op.create_index("ix_readings_captured_at", "readings", ["captured_at"], schema="sensor")


def downgrade() -> None:
    op.drop_index("ix_readings_captured_at", table_name="readings", schema="sensor")
    op.drop_index("ix_readings_sensor_id", table_name="readings", schema="sensor")
    op.drop_table("readings", schema="sensor")
    op.drop_index("ix_sensors_serial_number", table_name="sensors", schema="sensor")
    op.drop_index("ix_sensors_plot_id", table_name="sensors", schema="sensor")
    op.drop_table("sensors", schema="sensor")
