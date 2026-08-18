"""tenant.lead_mode + lead.released (modelos de negocio de leads)

Revision ID: 0003_lead_modes
Revises: 0002_leadhub
Create Date: 2026-07-27
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_lead_modes"
down_revision: Union[str, None] = "0002_leadhub"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tenant", sa.Column("lead_mode", sa.String(length=20), nullable=False, server_default="agency_managed"))
    op.add_column("lead", sa.Column("released", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.create_index("ix_lead_released", "lead", ["released"])


def downgrade() -> None:
    op.drop_index("ix_lead_released", table_name="lead")
    op.drop_column("lead", "released")
    op.drop_column("tenant", "lead_mode")
