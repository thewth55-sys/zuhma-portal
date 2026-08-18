"""tenant.enabled_modules (módulos habilitados por cliente)

Revision ID: 0009_tenant_modules
Revises: 0008_conversion_config
Create Date: 2026-08-17
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009_tenant_modules"
down_revision: Union[str, None] = "0008_conversion_config"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tenant", sa.Column("enabled_modules", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("tenant", "enabled_modules")
