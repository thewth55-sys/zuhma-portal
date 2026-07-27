"""esquema inicial del portal (tenant, app_user, plan, plan_quota, content_piece, audit)

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-27
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


user_role = sa.Enum("client", "zuhma_member", "admin", name="user_role")
content_status = sa.Enum("pending", "approved", "changes", "auto_approved", name="content_status")


def upgrade() -> None:
    op.create_table(
        "tenant",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("odoo_partner_id", sa.BigInteger(), nullable=False),
        sa.Column("plan_name", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("brand_primary", sa.String(length=9), nullable=True),
        sa.Column("logo_url", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("slug", name="uq_tenant_slug"),
        sa.UniqueConstraint("odoo_partner_id", name="uq_tenant_partner"),
    )
    op.create_index("ix_tenant_slug", "tenant", ["slug"])
    op.create_index("ix_tenant_partner", "tenant", ["odoo_partner_id"])

    op.create_table(
        "plan",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("code", name="uq_plan_code"),
    )

    op.create_table(
        "app_user",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("supabase_user_id", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("role", user_role, nullable=False, server_default="client"),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenant.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("supabase_user_id", name="uq_user_supabase"),
    )
    op.create_index("ix_app_user_supabase", "app_user", ["supabase_user_id"])
    op.create_index("ix_app_user_email", "app_user", ["email"])
    op.create_index("ix_app_user_tenant", "app_user", ["tenant_id"])

    op.create_table(
        "plan_quota",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("period", sa.String(length=7), nullable=False),
        sa.Column("metric", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_plan_quota_tenant", "plan_quota", ["tenant_id"])
    op.create_index("ix_plan_quota_period", "plan_quota", ["period"])

    op.create_table(
        "content_piece",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("preview_url", sa.String(length=512), nullable=True),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("status", content_status, nullable=False, server_default="pending"),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("deliver_date", sa.Date(), nullable=True),
        sa.Column("auto_approve_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("uploaded_by", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_content_tenant", "content_piece", ["tenant_id"])
    op.create_index("ix_content_status", "content_piece", ["status"])

    op.create_table(
        "impersonation_audit",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("admin_user_id", sa.Integer(), sa.ForeignKey("app_user.id"), nullable=False),
        sa.Column("admin_email", sa.String(length=255), nullable=False),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip", sa.String(length=64), nullable=True),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_admin", "impersonation_audit", ["admin_user_id"])
    op.create_index("ix_audit_tenant", "impersonation_audit", ["tenant_id"])


def downgrade() -> None:
    op.drop_table("impersonation_audit")
    op.drop_table("content_piece")
    op.drop_table("plan_quota")
    op.drop_table("app_user")
    op.drop_table("plan")
    op.drop_table("tenant")
    content_status.drop(op.get_bind(), checkfirst=True)
    user_role.drop(op.get_bind(), checkfirst=True)
