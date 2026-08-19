"""lead.deal_value + lead.revenue (cierre económico al ganar)

Revision ID: 0012_lead_won_fields
Revises: 0011_mfa
Create Date: 2026-08-18
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0012_lead_won_fields"
down_revision: Union[str, None] = "0011_mfa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("lead", sa.Column("deal_value", sa.Integer(), nullable=True))
    op.add_column("lead", sa.Column("revenue", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("lead", "revenue")
    op.drop_column("lead", "deal_value")
