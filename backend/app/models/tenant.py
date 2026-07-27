from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


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

    # Overrides de marca opcionales (logo, color) para white-label futuro.
    brand_primary: Mapped[str | None] = mapped_column(String(9), default=None)
    logo_url: Mapped[str | None] = mapped_column(String(512), default=None)

    users: Mapped[list["AppUser"]] = relationship(back_populates="tenant")  # noqa: F821
    quotas: Mapped[list["PlanQuota"]] = relationship(back_populates="tenant")  # noqa: F821
