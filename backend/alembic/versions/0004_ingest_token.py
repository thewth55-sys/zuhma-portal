"""tenant.ingest_token (webhook de ingesta de leads)

Revision ID: 0004_ingest_token
Revises: 0003_lead_modes
Create Date: 2026-08-17
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_ingest_token"
down_revision: Union[str, None] = "0003_lead_modes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tenant", sa.Column("ingest_token", sa.String(length=64), nullable=True))
    op.create_index("ix_tenant_ingest_token", "tenant", ["ingest_token"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_tenant_ingest_token", table_name="tenant")
    op.drop_column("tenant", "ingest_token")
