"""Implementación STUB del Lead Hub — datos de muestra tras el contrato real.

Sirve para desarrollar y ver las vistas Bandeja de leads / Atribución / embudo de
muestra mientras el Lead Hub real se construye. Los datos son deterministas (no
aleatorios) para que las pruebas y capturas sean estables.
"""

from __future__ import annotations

from app.leadhub.base import (
    AttributionKpis,
    FunnelStep,
    Lead,
    LeadHub,
    LeadKpis,
)

_LEADS: list[Lead] = [
    {
        "id": "LZ-20260727-A7F3K", "name": "Daniela Olvera", "affinity": 92,
        "channel": "Meta Ads", "status": "pending", "owner": "Ana Torres",
        "minutes_in_inbox": 12, "overdue": False,
        "description": "Interesada en franquiciar. Busca invertir más de $500k MXN.",
        "contacts": [{"kind": "phone", "value": "+52 155 6111 3534"}],
    },
    {
        "id": "LZ-20260726-B2M9P", "name": "Lizeth Ramírez", "affinity": 81,
        "channel": "Google Ads", "status": "pending", "owner": "Ana Torres",
        "minutes_in_inbox": 2160, "overdue": True,
        "description": "Solicitó costos de franquicia y requisitos. Alta afinidad sin atender.",
        "contacts": [{"kind": "phone", "value": "377 373 8738"}, {"kind": "mail", "value": "lizeth@correo.com"}],
    },
    {
        "id": "LZ-20260727-C5K1D", "name": "Gabriel Gardea", "affinity": 58,
        "channel": "WhatsApp", "status": "waiting", "owner": "Sin dueño",
        "minutes_in_inbox": 120, "overdue": False,
        "description": "Preguntó por el modelo de negocio. Afinidad media; conviene nutrir.",
        "contacts": [{"kind": "phone", "value": "+52 155 4467 8963"}],
    },
]


class StubLeadHub(LeadHub):
    def lead_kpis(self, tenant_partner_id: int) -> LeadKpis:
        pending = sum(1 for lead in _LEADS if lead["status"] == "pending")
        return {
            "pending": pending,
            "avg_response_hours": 8.0,
            "qualified_month": 63,
            "answered_under_24h_pct": 72,
        }

    def list_leads(self, tenant_partner_id: int, status: str | None = None) -> list[Lead]:
        if status and status != "all":
            return [lead for lead in _LEADS if lead["status"] == status]
        return list(_LEADS)

    def set_lead_status(self, tenant_partner_id: int, lead_id: str, status: str) -> Lead:
        for lead in _LEADS:
            if lead["id"] == lead_id:
                # En el stub no persistimos; devolvemos la pieza con el nuevo estado.
                return {**lead, "status": status}
        raise KeyError(lead_id)

    def attribution_kpis(self, tenant_partner_id: int) -> AttributionKpis:
        return {
            "capi_match_rate": 78,
            "gclid_coverage": 91,
            "leads_with_id": 142,
            "server_events": 486,
        }

    def commercial_funnel(self, tenant_partner_id: int) -> list[FunnelStep]:
        # "Embudo comercial" — SOLO MUESTRA (decisión de producto): datos de ejemplo.
        return [
            {"label": "Prospectos", "count": 420},
            {"label": "Calificados", "count": 142},
            {"label": "Oportunidad", "count": 63},
            {"label": "Cierre", "count": 18},
        ]
