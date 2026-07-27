from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Plan(Base, TimestampMixin):
    """Catálogo de planes (Growth B2B, Lite, A demanda…)."""

    __tablename__ = "plan"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(120))


class PlanQuota(Base, TimestampMixin):
    """Consumo del plan por tenant y periodo ("7 de 12 publicaciones").

    Lógica propia del panel — Odoo no modela esto. `period` en formato 'YYYY-MM'.
    """

    __tablename__ = "plan_quota"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), index=True)
    period: Mapped[str] = mapped_column(String(7), index=True)  # 'YYYY-MM'
    metric: Mapped[str] = mapped_column(String(64))  # p.ej. 'content_posts', 'reels', 'reports'
    label: Mapped[str] = mapped_column(String(120))
    used: Mapped[int] = mapped_column(Integer, default=0)
    total: Mapped[int] = mapped_column(Integer, default=0)

    tenant: Mapped["Tenant"] = relationship(back_populates="quotas")  # noqa: F821
