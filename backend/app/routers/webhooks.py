"""Webhooks de plataformas. Meta Lead Ads (leadgen) → Lead Hub, nativo (sin n8n).

Dos rutas:
  /webhooks/meta            → App GLOBAL de Zuhma (credenciales del entorno).
  /webhooks/meta/{token}    → App PROPIA del cliente (credenciales del tenant).
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.integrations import meta
from app.leadhub.repository import LeadRepository
from app.models import MetaPage, Tenant

logger = logging.getLogger("webhooks.meta")
router = APIRouter(prefix="/webhooks", tags=["webhooks"])
settings = get_settings()


def _challenge(request: Request, verify_token: str | None) -> PlainTextResponse:
    p = request.query_params
    if p.get("hub.mode") == "subscribe" and verify_token and p.get("hub.verify_token") == verify_token:
        return PlainTextResponse(p.get("hub.challenge", ""))
    raise HTTPException(status.HTTP_403_FORBIDDEN, "Verify token no coincide.")


def _process_leadgen(raw: bytes, db: Session) -> int:
    """Parsea el payload y crea los leads. Devuelve cuántos procesó."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cuerpo no es JSON.")

    processed = 0
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            if change.get("field") != "leadgen":
                continue
            value = change.get("value", {})
            page_id = str(value.get("page_id", ""))
            leadgen_id = value.get("leadgen_id")
            page = db.scalar(select(MetaPage).where(MetaPage.page_id == page_id, MetaPage.is_active.is_(True)))
            if not page or not leadgen_id:
                logger.warning("Lead de página no conectada page_id=%s", page_id)
                continue
            try:
                graph_lead = meta.fetch_lead(str(leadgen_id), page.page_access_token)
                payload = meta.map_lead_fields(graph_lead)
                tenant = db.get(Tenant, page.tenant_id)
                if tenant is not None:
                    LeadRepository(db, tenant).create(payload)
                    processed += 1
            except Exception:  # noqa: BLE001 — nunca fallar el webhook (Meta reintenta)
                logger.exception("Error procesando leadgen_id=%s", leadgen_id)
    return processed


# ---- App global de Zuhma ---- #

@router.get("/meta")
async def verify_meta(request: Request) -> PlainTextResponse:
    return _challenge(request, settings.meta_verify_token)


@router.post("/meta")
async def receive_meta(request: Request, db: Session = Depends(get_db)) -> dict:
    raw = await request.body()
    if not meta.verify_signature(raw, request.headers.get("X-Hub-Signature-256")):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Firma inválida.")
    return {"received": True, "processed": _process_leadgen(raw, db)}


# ---- App propia del cliente (por token) ---- #

@router.get("/meta/{token}")
async def verify_meta_client(token: str, request: Request, db: Session = Depends(get_db)) -> PlainTextResponse:
    tenant = db.scalar(select(Tenant).where(Tenant.meta_webhook_token == token))
    verify_token = tenant.meta_verify_token if tenant else settings.meta_verify_token
    return _challenge(request, verify_token)


@router.post("/meta/{token}")
async def receive_meta_client(token: str, request: Request, db: Session = Depends(get_db)) -> dict:
    tenant = db.scalar(select(Tenant).where(Tenant.meta_webhook_token == token))
    app_secret = tenant.meta_app_secret if tenant and tenant.meta_app_secret else None
    raw = await request.body()
    if not meta.verify_signature(raw, request.headers.get("X-Hub-Signature-256"), app_secret):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Firma inválida.")
    return {"received": True, "processed": _process_leadgen(raw, db)}
