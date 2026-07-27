from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class ImpersonationAudit(Base, TimestampMixin):
    """Registro de "ver como cliente" (suplantación admin).

    Requisito de seguridad (sección 8 del brief): toda suplantación queda auditada
    y marcada visualmente en el frontend. Se abre un registro al iniciar y se cierra
    (`ended_at`) al salir.
    """

    __tablename__ = "impersonation_audit"

    id: Mapped[int] = mapped_column(primary_key=True)
    admin_user_id: Mapped[int] = mapped_column(ForeignKey("app_user.id"), index=True)
    admin_email: Mapped[str] = mapped_column(String(255))
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), index=True)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    ip: Mapped[str | None] = mapped_column(String(64), default=None)
    reason: Mapped[str | None] = mapped_column(String(255), default=None)
