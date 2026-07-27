"""Seed de tenants piloto ↔ partners reales de Odoo.

Partner IDs verificados contra la cuenta real (2026-07-27). Idempotente: si el
tenant ya existe (por slug), actualiza sus datos en vez de duplicar.

Uso:
    python -m scripts.seed_tenants
"""

from __future__ import annotations

from sqlalchemy import select

from app.db import SessionLocal
from app.models import Plan, PlanQuota, Tenant

# (slug, nombre, odoo_partner_id, plan)
PILOT_TENANTS = [
    ("nextcore", "Nextcore Consulting, S.C.", 23, "Growth B2B"),
    ("cicadehp", "Grupo Cicadehp", 19, "Growth B2B"),
    ("hematia", "Hematia Retorno a la Salud", 184, "Growth"),
    ("elsa-victoria", "Elsa Victoria Hernández Ruiz", 355, "Lite"),
]

PLANS = [
    ("growth_b2b", "Growth B2B"),
    ("growth", "Growth"),
    ("lite", "Lite"),
    ("on_demand", "A demanda"),
]

# Consumo de muestra para la vista de Inicio / Plan (periodo actual).
SAMPLE_QUOTAS = [
    ("content_posts", "Publicaciones de contenido", 7, 12),
    ("reels", "Reels / historias", 5, 8),
    ("reports", "Reportes estratégicos", 1, 2),
    ("strategy_hours", "Horas de estrategia", 6, 10),
]
CURRENT_PERIOD = "2026-07"


def run() -> None:
    db = SessionLocal()
    try:
        for code, name in PLANS:
            if not db.scalar(select(Plan).where(Plan.code == code)):
                db.add(Plan(code=code, name=name))
        db.commit()

        for slug, name, partner_id, plan in PILOT_TENANTS:
            tenant = db.scalar(select(Tenant).where(Tenant.slug == slug))
            if tenant is None:
                tenant = Tenant(slug=slug, name=name, odoo_partner_id=partner_id, plan_name=plan)
                db.add(tenant)
                db.flush()
                print(f"  + tenant creado: {slug} → partner {partner_id}")
            else:
                tenant.name = name
                tenant.odoo_partner_id = partner_id
                tenant.plan_name = plan
                print(f"  ~ tenant actualizado: {slug} → partner {partner_id}")

            # Cuotas de muestra (solo si no hay ninguna para el periodo).
            has_quota = db.scalar(
                select(PlanQuota).where(
                    PlanQuota.tenant_id == tenant.id, PlanQuota.period == CURRENT_PERIOD
                )
            )
            if not has_quota:
                for metric, label, used, total in SAMPLE_QUOTAS:
                    db.add(
                        PlanQuota(
                            tenant_id=tenant.id, period=CURRENT_PERIOD,
                            metric=metric, label=label, used=used, total=total,
                        )
                    )
        db.commit()
        print("Seed completado.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
