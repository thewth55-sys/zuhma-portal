"""Contrato (interfaz) del Lead Hub — lo que el portal espera consumir.

Definido a partir del brief del producto (secciones 4.4 y 4.5). Todo método recibe
el `tenant_partner_id` (o slug) para que el Lead Hub, multi-tenant nativo, aísle por
cliente igual que el portal.
"""

from __future__ import annotations

from typing import Protocol, TypedDict


class LeadContact(TypedDict, total=False):
    kind: str  # phone | mail
    value: str


class Lead(TypedDict):
    id: str            # Lead ID único, p.ej. LZ-20260727-A7F3K
    name: str
    affinity: int      # % de afinidad 0..100
    channel: str       # Meta Ads | Google Ads | WhatsApp | Orgánico
    status: str        # pending | waiting | potential | discarded
    owner: str
    minutes_in_inbox: int
    overdue: bool
    description: str
    contacts: list[LeadContact]


class LeadKpis(TypedDict):
    pending: int
    avg_response_hours: float
    qualified_month: int
    answered_under_24h_pct: int


class AttributionKpis(TypedDict):
    capi_match_rate: int
    gclid_coverage: int
    leads_with_id: int
    server_events: int


class FunnelStep(TypedDict):
    label: str
    count: int


class LeadHub(Protocol):
    """Contrato estable. `stub` y `live` lo implementan de forma intercambiable."""

    def lead_kpis(self, tenant_partner_id: int) -> LeadKpis: ...

    def list_leads(self, tenant_partner_id: int, status: str | None = None) -> list[Lead]: ...

    def set_lead_status(self, tenant_partner_id: int, lead_id: str, status: str) -> Lead: ...

    def add_lead(self, tenant_partner_id: int, name: str, channel: str, contact: str) -> Lead: ...

    def attribution_kpis(self, tenant_partner_id: int) -> AttributionKpis: ...

    def commercial_funnel(self, tenant_partner_id: int) -> list[FunnelStep]: ...
