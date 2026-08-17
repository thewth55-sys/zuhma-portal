"""Seed de leads de muestra para el Lead Hub (tenant piloto Nextcore).

Idempotente: solo siembra si el tenant no tiene leads. Los datos ilustran los tres
niveles de propensidad (Alta/Media/Baja) usando el cuestionario de Nextcore.

Uso:
    python -m scripts.seed_leadhub
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.db import SessionLocal
from app.leadhub.repository import LeadRepository
from app.models import Lead, Tenant

SAMPLES = [
    {
        "contact_name": "Daniela Olvera", "cargo": "Directora de TI", "phone": "+52 155 6111 3534",
        "email": "daniela@empresa.mx", "company_name": "Grupo Franquicias", "company_size": "+150",
        "website": "grupofranquicias.mx", "channel": "Meta Ads",
        "description": "Interesada en migrar a Microsoft 365 para +100 usuarios.",
        "answers": {
            "tamano_proyecto": "gt100", "tiempo_adquisicion": "este_trimestre", "presupuesto": "si",
            "quien_decide": "individual", "es_renovacion": "no", "tamano_empresa": "gt150",
            "tienen_partner": "no", "cantidad_usuarios": 120, "esquema": "anual", "microsoft": True,
        },
        "gclid": "", "utm_source": "meta", "utm_campaign": "franquicias-q3",
    },
    {
        "contact_name": "Lizeth Ramírez", "cargo": "Gerente de Compras", "phone": "377 373 8738",
        "email": "lizeth@correo.com", "company_name": "Retail Norte", "company_size": "80–150",
        "channel": "Google Ads",
        "description": "Solicitó costos y requisitos. Alta afinidad sin atender.",
        "answers": {
            "tamano_proyecto": "80_100", "tiempo_adquisicion": "proximo_trimestre", "presupuesto": "si",
            "quien_decide": "comite", "es_renovacion": "no", "tamano_empresa": "80_150",
            "tienen_partner": "no", "cantidad_usuarios": 90, "esquema": "mensual",
        },
        "gclid": "Cj0KCQ-demo-gclid", "utm_source": "google", "utm_campaign": "search-brand",
        "_age_hours": 36,  # para que aparezca "vencido" en la bandeja
    },
    {
        "contact_name": "Gabriel Gardea", "cargo": "Coordinador", "phone": "+52 155 4467 8963",
        "company_name": "Instituto Educativo", "company_size": "<80", "channel": "WhatsApp",
        "description": "Preguntó por el modelo de negocio. Conviene nutrir antes de llamar.",
        "answers": {
            "tamano_proyecto": "lt80", "tiempo_adquisicion": "indefinido", "presupuesto": "no",
            "quien_decide": "no_influye", "es_renovacion": "si", "tamano_empresa": "lt80",
            "tienen_partner": "si", "sector": ["educacion"], "cantidad_usuarios": 40,
        },
    },
]


def run() -> None:
    db = SessionLocal()
    try:
        tenant = db.scalar(select(Tenant).where(Tenant.slug == "nextcore"))
        if tenant is None:
            print("No existe el tenant 'nextcore'. Corre primero scripts.seed_tenants.")
            return
        if db.scalar(select(Lead).where(Lead.tenant_id == tenant.id)):
            print("El tenant ya tiene leads; no se siembra de nuevo.")
            return

        repo = LeadRepository(db, tenant)
        for s in SAMPLES:
            age = s.pop("_age_hours", None)
            detail = repo.create(s)
            print(f"  + lead {detail['id']} · {detail['name']} · propensidad {detail['propensity_score']} ({detail['propensity_band']})")
            if age:
                lead = db.scalar(select(Lead).where(Lead.lead_id == detail["id"]))
                lead.created_at = datetime.now(timezone.utc) - timedelta(hours=age)
                db.commit()
        print("Seed del Lead Hub completado.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
