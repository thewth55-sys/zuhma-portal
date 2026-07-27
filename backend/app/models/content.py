from __future__ import annotations

import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class ContentStatus(str, enum.Enum):
    pending = "pending"    # espera aprobación del cliente
    approved = "approved"
    changes = "changes"    # el cliente pidió cambios
    auto_approved = "auto_approved"  # sin feedback en el plazo → aprobado por regla


class ContentPiece(Base, TimestampMixin):
    """Pieza de contenido para el flujo de Aprobaciones (módulo PROPIO, no Odoo).

    Regla de negocio: si `auto_approve_at` pasa sin feedback, un job la marca
    `auto_approved` (2 días hábiles por defecto; configurable por tenant en Fase 2).
    """

    __tablename__ = "content_piece"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), index=True)

    kind: Mapped[str] = mapped_column(String(32))  # post | reel | story
    title: Mapped[str] = mapped_column(String(255))
    preview_url: Mapped[str | None] = mapped_column(String(512), default=None)
    caption: Mapped[str | None] = mapped_column(Text, default=None)

    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus, name="content_status"), default=ContentStatus.pending, index=True
    )
    feedback: Mapped[str | None] = mapped_column(Text, default=None)

    deliver_date: Mapped[date | None] = mapped_column(Date, default=None)
    auto_approve_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    uploaded_by: Mapped[str | None] = mapped_column(String(255), default=None)  # miembro Zuhma
