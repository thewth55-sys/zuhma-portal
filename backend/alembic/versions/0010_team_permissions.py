"""app_user: active, permissions, managed_client_ids (equipo interno)

Revision ID: 0010_team_permissions
Revises: 0009_tenant_modules
Create Date: 2026-08-17
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010_team_permissions"
down_revision: Union[str, None] = "0009_tenant_modules"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("app_user", sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("app_user", sa.Column("permissions", postgresql.JSONB(), nullable=True))
    op.add_column("app_user", sa.Column("managed_client_ids", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("app_user", "managed_client_ids")
    op.drop_column("app_user", "permissions")
    op.drop_column("app_user", "active")
