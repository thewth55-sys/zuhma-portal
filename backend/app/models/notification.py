"""Notificaciones internas del portal + preferencias de alerta por cliente.

`Notification` es una alerta dirigida a UN usuario (campana del portal). Hoy se genera
al ingresar un lead nuevo, y se envía en paralelo por correo. `LeadAlertMute` guarda el
silenciado por (usuario, cliente): si existe la fila, ese usuario NO recibe alertas de
ese cliente. Ausencia de fila = suscrito (default ON).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Notification(Base, TimestampMixin):
    __tablename__ = "notification"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("app_user.id"), index=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenant.id"), default=None, index=True)

    kind: Mapped[str] = mapped_column(String(32), default="new_lead")
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text, default="")
    # Código del lead (LZ-…) para hacer deep-link sin acoplar un FK que rompa al borrar.
    lead_code: Mapped[str | None] = mapped_column(String(48), default=None)

    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)


class LeadAlertMute(Base, TimestampMixin):
    """Fila presente = el usuario silenció las alertas de leads de ese cliente."""

    __tablename__ = "lead_alert_mute"
    __table_args__ = (UniqueConstraint("user_id", "tenant_id", name="uq_alert_mute_user_tenant"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("app_user.id"), index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), index=True)
