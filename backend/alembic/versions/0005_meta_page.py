"""meta_page (páginas de Meta conectadas para Lead Ads)

Revision ID: 0005_meta_page
Revises: 0004_ingest_token
Create Date: 2026-08-17
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_meta_page"
down_revision: Union[str, None] = "0004_ingest_token"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "meta_page",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("page_id", sa.String(length=64), nullable=False),
        sa.Column("page_name", sa.String(length=255), nullable=True),
        sa.Column("page_access_token", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("page_id", name="uq_meta_page_page_id"),
    )
    op.create_index("ix_meta_page_tenant", "meta_page", ["tenant_id"])
    op.create_index("ix_meta_page_page_id", "meta_page", ["page_id"])


def downgrade() -> None:
    op.drop_table("meta_page")
