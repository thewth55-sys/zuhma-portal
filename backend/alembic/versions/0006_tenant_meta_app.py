"""App de Meta propia por cliente (opcional)

Revision ID: 0006_tenant_meta_app
Revises: 0005_meta_page
Create Date: 2026-08-17
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006_tenant_meta_app"
down_revision: Union[str, None] = "0005_meta_page"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tenant", sa.Column("meta_app_id", sa.String(length=64), nullable=True))
    op.add_column("tenant", sa.Column("meta_app_secret", sa.String(length=255), nullable=True))
    op.add_column("tenant", sa.Column("meta_verify_token", sa.String(length=120), nullable=True))
    op.add_column("tenant", sa.Column("meta_webhook_token", sa.String(length=64), nullable=True))
    op.create_index("ix_tenant_meta_webhook_token", "tenant", ["meta_webhook_token"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_tenant_meta_webhook_token", table_name="tenant")
    op.drop_column("tenant", "meta_webhook_token")
    op.drop_column("tenant", "meta_verify_token")
    op.drop_column("tenant", "meta_app_secret")
    op.drop_column("tenant", "meta_app_id")
