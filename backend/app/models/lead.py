"""Modelos del Lead Hub (viven en la base PROPIA del portal, no en Odoo).

El portal es el sistema central de leads y medición de conversiones. Un Lead lleva:
contacto/empresa, respuestas del cuestionario (configurable por cliente → JSON),
propensidad calculada, atribución (gclid/fbclid/fbc/fbp/utm) y sus eventos de
conversión hacia Meta CAPI / Google Ads.
"""

from __future__ import annotations

import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class LeadStatus(str, enum.Enum):
    pending = "pending"      # sin atender
    waiting = "waiting"      # en espera / agendado
    potential = "potential"  # calificado como potencial
    discarded = "discarded"  # no potencial


class EventStatus(str, enum.Enum):
    queued = "queued"    # modelado, pendiente de enviar (falta credencial o motor)
    sent = "sent"
    failed = "failed"


class Lead(Base, TimestampMixin):
    __tablename__ = "lead"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), index=True)
    lead_id: Mapped[str] = mapped_column(String(48), unique=True, index=True)  # LZ-YYYYMMDD-XXXXX

    # Contacto y empresa (universales)
    contact_name: Mapped[str] = mapped_column(String(255))
    cargo: Mapped[str | None] = mapped_column(String(160), default=None)
    email: Mapped[str | None] = mapped_column(String(255), default=None)
    phone: Mapped[str | None] = mapped_column(String(64), default=None)
    company_name: Mapped[str | None] = mapped_column(String(255), default=None)
    company_size: Mapped[str | None] = mapped_column(String(64), default=None)
    website: Mapped[str | None] = mapped_column(String(255), default=None)

    channel: Mapped[str] = mapped_column(String(64), default="Orgánico")  # Meta Ads/Google Ads/WhatsApp…
    owner: Mapped[str | None] = mapped_column(String(160), default="Sin dueño")
    status: Mapped[LeadStatus] = mapped_column(
        Enum(LeadStatus, name="lead_status"), default=LeadStatus.pending, index=True
    )
    description: Mapped[str | None] = mapped_column(Text, default=None)   # contexto/requerimiento
    session_date: Mapped[date | None] = mapped_column(Date, default=None)

    # Respuestas del cuestionario configurable por cliente (key → valor).
    answers: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Propensidad calculada a partir de answers + config del tenant.
    propensity_score: Mapped[int | None] = mapped_column(Integer, default=None)
    propensity_band: Mapped[str | None] = mapped_column(String(16), default=None)  # alta/media/baja

    # Atribución (para CAPI / Google Ads offline)
    gclid: Mapped[str | None] = mapped_column(String(255), default=None)
    fbclid: Mapped[str | None] = mapped_column(String(255), default=None)
    fbc: Mapped[str | None] = mapped_column(String(255), default=None)
    fbp: Mapped[str | None] = mapped_column(String(255), default=None)
    utm_source: Mapped[str | None] = mapped_column(String(160), default=None)
    utm_medium: Mapped[str | None] = mapped_column(String(160), default=None)
    utm_campaign: Mapped[str | None] = mapped_column(String(160), default=None)

    events: Mapped[list["LeadEvent"]] = relationship(back_populates="lead", cascade="all, delete-orphan")
    activities: Mapped[list["LeadActivity"]] = relationship(back_populates="lead", cascade="all, delete-orphan")


class LeadEvent(Base, TimestampMixin):
    """Evento de conversión hacia plataformas (Meta CAPI / Google Ads offline)."""

    __tablename__ = "lead_event"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_pk: Mapped[int] = mapped_column(ForeignKey("lead.id"), index=True)

    event_name: Mapped[str] = mapped_column(String(64))  # Lead | QualifiedLead | Purchase …
    destination: Mapped[str] = mapped_column(String(16))  # meta | google | both
    event_id: Mapped[str] = mapped_column(String(64))     # para deduplicar contra el pixel
    status: Mapped[EventStatus] = mapped_column(Enum(EventStatus, name="event_status"), default=EventStatus.queued)
    value: Mapped[int | None] = mapped_column(Integer, default=None)  # valor económico por etapa
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    response: Mapped[str | None] = mapped_column(Text, default=None)

    lead: Mapped["Lead"] = relationship(back_populates="events")


class LeadActivity(Base, TimestampMixin):
    """Timeline del lead: creación, cambios de etapa, correos, notas."""

    __tablename__ = "lead_activity"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_pk: Mapped[int] = mapped_column(ForeignKey("lead.id"), index=True)
    kind: Mapped[str] = mapped_column(String(32))  # created | stage | email | note | event
    text: Mapped[str] = mapped_column(Text)

    lead: Mapped["Lead"] = relationship(back_populates="activities")


class LeadConfig(Base, TimestampMixin):
    """Configuración del Lead Hub POR CLIENTE: cuestionario, reglas de scoring y
    mapeo etapa→evento de conversión. Guardado como JSON para editarlo sin migrar.
    """

    __tablename__ = "lead_config"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), unique=True, index=True)
    config: Mapped[dict] = mapped_column(JSONB, default=dict)
