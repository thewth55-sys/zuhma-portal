from __future__ import annotations

import enum

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class UserRole(str, enum.Enum):
    client = "client"            # cliente final: solo ve SU tenant
    zuhma_member = "zuhma_member"  # equipo Zuhma: puede ver clientes asignados
    admin = "admin"              # administración total + "ver como cliente"


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

    # Un cliente pertenece a un tenant. Los admin/zuhma_member pueden no tener tenant fijo.
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenant.id"), default=None, index=True)
    tenant: Mapped["Tenant | None"] = relationship(back_populates="users")  # noqa: F821
