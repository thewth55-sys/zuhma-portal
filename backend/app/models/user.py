from __future__ import annotations

import enum

from sqlalchemy import Boolean, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class UserRole(str, enum.Enum):
    client = "client"            # cliente final: solo ve SU tenant
    zuhma_member = "zuhma_member"  # equipo Zuhma: permisos granulares + clientes asignados
    admin = "admin"              # administración total


# Permisos granulares para usuarios internos (el rol admin los tiene todos).
ALL_PERMISSIONS = [
    "manage_clients",   # crear/editar clientes
    "manage_leads",     # gestionar leads, conversiones, fuentes
    "upload_content",   # subir contenido a aprobación
    "manage_tasks",     # tareas de Odoo
    "manage_billing",   # facturación
    "manage_team",      # gestionar el equipo interno
]


class AppUser(Base, TimestampMixin):
    """Usuario del portal. La identidad la lleva Supabase Auth (`supabase_user_id`);
    aquí guardamos rol y a qué tenant pertenece.
    """

    __tablename__ = "app_user"

    id: Mapped[int] = mapped_column(primary_key=True)
    supabase_user_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    full_name: Mapped[str | None] = mapped_column(String(255), default=None)

    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), default=UserRole.client)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Interno: permisos granulares y clientes asignados (null = todos).
    permissions: Mapped[list | None] = mapped_column(JSONB, default=None)
    managed_client_ids: Mapped[list | None] = mapped_column(JSONB, default=None)

    # Un cliente pertenece a un tenant. Los admin/zuhma_member pueden no tener tenant fijo.
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenant.id"), default=None, index=True)
    tenant: Mapped["Tenant | None"] = relationship(back_populates="users")  # noqa: F821

    @property
    def effective_permissions(self) -> list[str]:
        if self.role == UserRole.admin:
            return list(ALL_PERMISSIONS)
        return list(self.permissions or [])

    def has_perm(self, perm: str) -> bool:
        return self.role == UserRole.admin or perm in (self.permissions or [])
