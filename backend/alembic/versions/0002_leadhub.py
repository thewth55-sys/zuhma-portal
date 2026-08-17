"""Lead Hub: lead, lead_event, lead_activity, lead_config

Revision ID: 0002_leadhub
Revises: 0001_initial
Create Date: 2026-07-27
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_leadhub"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

lead_status = sa.Enum("pending", "waiting", "potential", "discarded", name="lead_status")
event_status = sa.Enum("queued", "sent", "failed", name="event_status")


def upgrade() -> None:
    op.create_table(
        "lead",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("lead_id", sa.String(length=48), nullable=False),
        sa.Column("contact_name", sa.String(length=255), nullable=False),
        sa.Column("cargo", sa.String(length=160), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column("company_size", sa.String(length=64), nullable=True),
        sa.Column("website", sa.String(length=255), nullable=True),
        sa.Column("channel", sa.String(length=64), nullable=False, server_default="Orgánico"),
        sa.Column("owner", sa.String(length=160), nullable=True, server_default="Sin dueño"),
        sa.Column("status", lead_status, nullable=False, server_default="pending"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("session_date", sa.Date(), nullable=True),
        sa.Column("answers", postgresql.JSONB(), nullable=True),
        sa.Column("propensity_score", sa.Integer(), nullable=True),
        sa.Column("propensity_band", sa.String(length=16), nullable=True),
        sa.Column("gclid", sa.String(length=255), nullable=True),
        sa.Column("fbclid", sa.String(length=255), nullable=True),
        sa.Column("fbc", sa.String(length=255), nullable=True),
        sa.Column("fbp", sa.String(length=255), nullable=True),
        sa.Column("utm_source", sa.String(length=160), nullable=True),
        sa.Column("utm_medium", sa.String(length=160), nullable=True),
        sa.Column("utm_campaign", sa.String(length=160), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("lead_id", name="uq_lead_lead_id"),
    )
    op.create_index("ix_lead_tenant", "lead", ["tenant_id"])
    op.create_index("ix_lead_lead_id", "lead", ["lead_id"])
    op.create_index("ix_lead_status", "lead", ["status"])

    op.create_table(
        "lead_event",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lead_pk", sa.Integer(), sa.ForeignKey("lead.id"), nullable=False),
        sa.Column("event_name", sa.String(length=64), nullable=False),
        sa.Column("destination", sa.String(length=16), nullable=False),
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("status", event_status, nullable=False, server_default="queued"),
        sa.Column("value", sa.Integer(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("response", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_lead_event_lead", "lead_event", ["lead_pk"])

    op.create_table(
        "lead_activity",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lead_pk", sa.Integer(), sa.ForeignKey("lead.id"), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_lead_activity_lead", "lead_activity", ["lead_pk"])

    op.create_table(
        "lead_config",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("config", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", name="uq_lead_config_tenant"),
    )
    op.create_index("ix_lead_config_tenant", "lead_config", ["tenant_id"])


def downgrade() -> None:
    op.drop_table("lead_config")
    op.drop_table("lead_activity")
    op.drop_table("lead_event")
    op.drop_table("lead")
    event_status.drop(op.get_bind(), checkfirst=True)
    lead_status.drop(op.get_bind(), checkfirst=True)
