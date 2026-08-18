"""Ingesta pública de leads (webhook) — punto único de entrada al Lead Hub.

Aquí llegan los leads de TODOS los orígenes de paid media, vía el token del cliente:
  - Meta Lead Ads (Meta → n8n → este webhook)
  - Chatwoot self-host (Chatwoot → n8n → este webhook)
  - WordPress (Fluent Forms / Contact Form 7 → snippet + webhook → aquí)
  - n8n (tus flujos existentes form→lead, chatwoot/whatsapp)

Seguridad: gated por el token opaco del cliente en la URL (no expone credenciales).
El token identifica al tenant; el lead se crea acotado a ese cliente con su atribución.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.leadhub.repository import LeadRepository
from app.models import Tenant

router = APIRouter(prefix="/ingest", tags=["ingest"])


class IngestLead(BaseModel):
    # Contacto / empresa
    contact_name: str
    cargo: str | None = None
    email: str | None = None
    phone: str | None = None
    company_name: str | None = None
    company_size: str | None = None
    website: str | None = None
    description: str | None = None
    # Origen
    channel: str | None = None          # Meta Ads | Google Ads | WhatsApp | WordPress | Orgánico
    source: str | None = None           # etiqueta libre del origen (form_id, inbox…)
    answers: dict = {}
    # Atribución (la captura el snippet JS: gclid/fbclid/fbc/fbp/utm)
    gclid: str | None = None
    fbclid: str | None = None
    fbc: str | None = None
    fbp: str | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None


@router.post("/{token}/lead", status_code=status.HTTP_201_CREATED)
def ingest_lead(token: str, body: IngestLead, db: Session = Depends(get_db)) -> dict:
    tenant = db.scalar(select(Tenant).where(Tenant.ingest_token == token, Tenant.is_active.is_(True)))
    if tenant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Token de ingesta no válido.")
    if not body.contact_name.strip():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "contact_name es obligatorio.")

    payload = body.model_dump()
    if not payload.get("channel"):
        payload["channel"] = "Orgánico"
    detail = LeadRepository(db, tenant).create(payload)
    return {"ok": True, "lead_id": detail["id"], "tenant": tenant.slug}
