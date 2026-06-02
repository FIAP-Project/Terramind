"""initial alert schema

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
    op.execute("CREATE SCHEMA IF NOT EXISTS alert")

    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("plot_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sensor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("rule_id", sa.String(length=64), nullable=False),
        sa.Column("message", sa.String(length=255), nullable=False),
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="alert",
    )
    op.create_index("ix_alerts_plot_id", "alerts", ["plot_id"], schema="alert")
    op.create_index("ix_alerts_sensor_id", "alerts", ["sensor_id"], schema="alert")
    op.create_index("ix_alerts_severity", "alerts", ["severity"], schema="alert")


def downgrade() -> None:
    op.drop_index("ix_alerts_severity", table_name="alerts", schema="alert")
    op.drop_index("ix_alerts_sensor_id", table_name="alerts", schema="alert")
    op.drop_index("ix_alerts_plot_id", table_name="alerts", schema="alert")
    op.drop_table("alerts", schema="alert")
