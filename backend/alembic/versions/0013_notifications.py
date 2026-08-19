"""notification + lead_alert_mute (alertas de lead nuevo)

Revision ID: 0013_notifications
Revises: 0012_lead_won_fields
Create Date: 2026-08-18
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0013_notifications"
down_revision: Union[str, None] = "0012_lead_won_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notification",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("app_user.id"), nullable=False),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenant.id"), nullable=True),
        sa.Column("kind", sa.String(length=32), nullable=False, server_default="new_lead"),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False, server_default=""),
        sa.Column("lead_code", sa.String(length=48), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_notification_user", "notification", ["user_id"])
    op.create_index("ix_notification_tenant", "notification", ["tenant_id"])

    op.create_table(
        "lead_alert_mute",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("app_user.id"), nullable=False),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "tenant_id", name="uq_alert_mute_user_tenant"),
    )
    op.create_index("ix_lead_alert_mute_user", "lead_alert_mute", ["user_id"])
    op.create_index("ix_lead_alert_mute_tenant", "lead_alert_mute", ["tenant_id"])


def downgrade() -> None:
    op.drop_table("lead_alert_mute")
    op.drop_table("notification")
