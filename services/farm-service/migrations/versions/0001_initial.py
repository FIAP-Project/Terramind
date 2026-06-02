"""initial farm schema

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
    op.execute("CREATE SCHEMA IF NOT EXISTS farm")

    op.create_table(
        "crops",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=80), nullable=False, unique=True),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("optimal_humidity_min", sa.Numeric(5, 2), nullable=False),
        sa.Column("optimal_humidity_max", sa.Numeric(5, 2), nullable=False),
        sa.Column("optimal_temp_min", sa.Numeric(5, 2), nullable=False),
        sa.Column("optimal_temp_max", sa.Numeric(5, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="farm",
    )
    op.create_index("ix_crops_name", "crops", ["name"], unique=True, schema="farm")

    op.create_table(
        "farms",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("area_ha", sa.Numeric(10, 2), nullable=False),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="farm",
    )
    op.create_index("ix_farms_owner_user_id", "farms", ["owner_user_id"], schema="farm")

    op.create_table(
        "plots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("farm_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("crop_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("area_ha", sa.Numeric(10, 2), nullable=False),
        sa.Column("planted_at", sa.Date(), nullable=True),
        sa.Column("expected_harvest_at", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["farm_id"], ["farm.farms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["crop_id"], ["farm.crops.id"], ondelete="SET NULL"),
        schema="farm",
    )
    op.create_index("ix_plots_farm_id", "plots", ["farm_id"], schema="farm")
    op.create_index("ix_plots_crop_id", "plots", ["crop_id"], schema="farm")

    # Seed inicial de culturas comuns no Brasil
    op.execute(
        """
        INSERT INTO farm.crops
          (id, name, description, optimal_humidity_min, optimal_humidity_max, optimal_temp_min, optimal_temp_max)
        VALUES
          (gen_random_uuid(), 'milho',  'Zea mays',           50, 75, 18, 32),
          (gen_random_uuid(), 'soja',   'Glycine max',        50, 70, 20, 30),
          (gen_random_uuid(), 'café',   'Coffea arabica',     60, 80, 18, 24),
          (gen_random_uuid(), 'cana',   'Saccharum officinarum', 60, 80, 21, 33),
          (gen_random_uuid(), 'algodão','Gossypium hirsutum', 50, 70, 21, 32);
        """
    )


def downgrade() -> None:
    op.drop_index("ix_plots_crop_id", table_name="plots", schema="farm")
    op.drop_index("ix_plots_farm_id", table_name="plots", schema="farm")
    op.drop_table("plots", schema="farm")
    op.drop_index("ix_farms_owner_user_id", table_name="farms", schema="farm")
    op.drop_table("farms", schema="farm")
    op.drop_index("ix_crops_name", table_name="crops", schema="farm")
    op.drop_table("crops", schema="farm")
