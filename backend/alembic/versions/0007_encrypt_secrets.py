"""Ensancha columnas de secretos a Text (para valores cifrados con Fernet)

Revision ID: 0007_encrypt_secrets
Revises: 0006_tenant_meta_app
Create Date: 2026-08-17
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007_encrypt_secrets"
down_revision: Union[str, None] = "0006_tenant_meta_app"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # El valor cifrado (Fernet + prefijo) es más largo que el secreto original.
    op.alter_column("tenant", "meta_app_secret", type_=sa.Text(), existing_nullable=True)
    op.alter_column("meta_page", "page_access_token", type_=sa.Text(), existing_nullable=False)


def downgrade() -> None:
    op.alter_column("tenant", "meta_app_secret", type_=sa.String(length=255), existing_nullable=True)
    op.alter_column("meta_page", "page_access_token", type_=sa.Text(), existing_nullable=False)
