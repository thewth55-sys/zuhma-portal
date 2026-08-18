"""Webhooks de plataformas. Meta Lead Ads (leadgen) → Lead Hub, nativo (sin n8n)."""

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


@router.get("/meta")
async def verify_meta(request: Request) -> PlainTextResponse:
    """Verificación del webhook: Meta manda hub.challenge al registrar la URL."""
    p = request.query_params
    if p.get("hub.mode") == "subscribe" and p.get("hub.verify_token") == settings.meta_verify_token and settings.meta_verify_token:
        return PlainTextResponse(p.get("hub.challenge", ""))
    raise HTTPException(status.HTTP_403_FORBIDDEN, "Verify token no coincide.")


@router.post("/meta")
async def receive_meta(request: Request, db: Session = Depends(get_db)) -> dict:
    raw = await request.body()
    if not meta.verify_signature(raw, request.headers.get("X-Hub-Signature-256")):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Firma inválida.")

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

    # Siempre 200 para que Meta no reintente en bucle.
    return {"received": True, "processed": processed}
