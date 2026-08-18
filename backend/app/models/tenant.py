from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.security.types import EncryptedString


class Tenant(Base, TimestampMixin):
    """Un cliente de Zuhma. Mapea 1:1 con la EMPRESA (res.partner) en Odoo.

    `odoo_partner_id` es la clave del aislamiento: todas las consultas a Odoo de
    este tenant se acotan con `partner_id child_of odoo_partner_id`.
    """

    __tablename__ = "tenant"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    odoo_partner_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)

    plan_name: Mapped[str | None] = mapped_column(String(120), default=None)
    status: Mapped[str] = mapped_column(String(32), default="active")  # active | paused | churned
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Modelo de negocio de leads:
    #   agency_managed → Zuhma califica; el cliente ve solo los leads LIBERADOS (Nextcore).
    #   client_managed → el cliente ve y califica todos; nacen liberados (Cicadehp).
    lead_mode: Mapped[str] = mapped_column(String(20), default="agency_managed")

    # Token opaco para la ingesta de leads por webhook (Meta/Chatwoot/WordPress/n8n → Lead Hub).
    ingest_token: Mapped[str | None] = mapped_column(String(64), unique=True, index=True, default=None)

    # App de Meta PROPIA del cliente (opcional). Si está, sus páginas usan estas
    # credenciales y una URL de webhook dedicada (meta_webhook_token). Si no, se usa la
    # App global de Zuhma. NOTA: el secret es sensible; cifrar en reposo a futuro.
    meta_app_id: Mapped[str | None] = mapped_column(String(64), default=None)
    meta_app_secret: Mapped[str | None] = mapped_column(EncryptedString, default=None)
    meta_verify_token: Mapped[str | None] = mapped_column(String(120), default=None)
    meta_webhook_token: Mapped[str | None] = mapped_column(String(64), unique=True, index=True, default=None)

    # Overrides de marca opcionales (logo, color) para white-label futuro.
    brand_primary: Mapped[str | None] = mapped_column(String(9), default=None)
    logo_url: Mapped[str | None] = mapped_column(String(512), default=None)

    users: Mapped[list["AppUser"]] = relationship(back_populates="tenant")  # noqa: F821
    quotas: Mapped[list["PlanQuota"]] = relationship(back_populates="tenant")  # noqa: F821
