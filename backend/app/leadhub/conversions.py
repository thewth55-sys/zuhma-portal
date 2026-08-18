"""Despachador de conversiones: envía los LeadEvent 'queued' a Meta CAPI / Google Ads.

Se llama tras calificar/liberar un lead (y manualmente desde el detalle). Cada evento
se marca como 'sent' o 'failed' con la respuesta; nunca lanza (no debe romper el flujo).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.integrations import capi, google_ads
from app.models import ConversionConfig, EventStatus, Lead, Tenant

logger = logging.getLogger("conversions")


def _config(db: Session, tenant_id: int) -> ConversionConfig | None:
    return db.scalar(select(ConversionConfig).where(ConversionConfig.tenant_id == tenant_id))


def flush_lead(db: Session, tenant: Tenant, lead_id: str) -> dict:
    """Intenta enviar los eventos en cola de un lead. Devuelve un resumen."""
    lead = db.scalar(
        select(Lead).where(Lead.tenant_id == tenant.id, Lead.lead_id == lead_id)
        .options(selectinload(Lead.events))
    )
    if lead is None:
        return {"sent": 0, "failed": 0, "skipped": 0}

    config = _config(db, tenant.id)
    sent = failed = skipped = 0

    for event in lead.events:
        if event.status != EventStatus.queued:
            continue
        dest = event.destination  # meta | google | both
        results: list[tuple[str, bool, str]] = []

        if dest in ("meta", "both"):
            if config and config.meta_ready:
                ok, detail = capi.send(config, lead, event)
                results.append(("meta", ok, detail))
            else:
                results.append(("meta", False, "Meta CAPI no configurado para el cliente."))

        if dest in ("google", "both"):
            if config and config.google_ready:
                ok, detail = google_ads.send(config, lead, event)
                results.append(("google", ok, detail))
            else:
                results.append(("google", False, "Google Ads no configurado para el cliente."))

        # 'both' → basta que UNO tenga éxito para marcar enviado; si no, failed.
        any_ok = any(ok for _, ok, _ in results)
        event.response = " | ".join(f"{d}: {'ok' if ok else 'x'} {msg}" for d, ok, msg in results)[:1000]
        if any_ok:
            event.status = EventStatus.sent
            event.sent_at = datetime.now(timezone.utc)
            sent += 1
        else:
            event.status = EventStatus.failed
            failed += 1

    db.commit()
    return {"sent": sent, "failed": failed, "skipped": skipped}
