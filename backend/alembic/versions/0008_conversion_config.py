"""conversion_config (credenciales CAPI / Google Ads por cliente)

Revision ID: 0008_conversion_config
Revises: 0007_encrypt_secrets
Create Date: 2026-08-17
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008_conversion_config"
down_revision: Union[str, None] = "0007_encrypt_secrets"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "conversion_config",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("meta_pixel_id", sa.String(length=64), nullable=True),
        sa.Column("meta_capi_token", sa.Text(), nullable=True),
        sa.Column("meta_test_event_code", sa.String(length=64), nullable=True),
        sa.Column("google_customer_id", sa.String(length=32), nullable=True),
        sa.Column("google_login_customer_id", sa.String(length=32), nullable=True),
        sa.Column("google_conversion_action_id", sa.String(length=64), nullable=True),
        sa.Column("google_developer_token", sa.Text(), nullable=True),
        sa.Column("google_client_id", sa.String(length=255), nullable=True),
        sa.Column("google_client_secret", sa.Text(), nullable=True),
        sa.Column("google_refresh_token", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", name="uq_conversion_config_tenant"),
    )
    op.create_index("ix_conversion_config_tenant", "conversion_config", ["tenant_id"])


def downgrade() -> None:
    op.drop_table("conversion_config")
