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


def flush_tenant_queued(db: Session, tenant: Tenant, limit: int = 300) -> dict:
    """Reintenta los eventos pendientes de los leads del cliente (al configurar credenciales)."""
    lead_ids = db.scalars(
        select(Lead.lead_id).where(Lead.tenant_id == tenant.id).order_by(Lead.created_at.desc()).limit(limit)
    ).all()
    total = {"sent": 0, "failed": 0, "skipped": 0}
    for lid in lead_ids:
        r = flush_lead(db, tenant, lid)
        for k in total:
            total[k] += r[k]
    return total


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
        if event.status == EventStatus.sent:  # ya enviado; reintenta queued Y failed
            continue
        dest = event.destination  # meta | google | both
        # outcome: "ok" (enviado), "failed" (intentado y falló), "skipped" (sin credenciales)
        results: list[tuple[str, str, str]] = []

        if dest in ("meta", "both"):
            if config and config.meta_ready:
                ok, detail = capi.send(config, lead, event)
                results.append(("meta", "ok" if ok else "failed", detail))
            else:
                results.append(("meta", "skipped", "Meta CAPI sin configurar."))

        if dest in ("google", "both"):
            if config and config.google_ready:
                ok, detail = google_ads.send(config, lead, event)
                results.append(("google", "ok" if ok else "failed", detail))
            else:
                results.append(("google", "skipped", "Google Ads sin configurar."))

        any_ok = any(o == "ok" for _, o, _ in results)
        attempted = any(o in ("ok", "failed") for _, o, _ in results)
        event.response = " | ".join(f"{d}: {o} — {msg}" for d, o, msg in results)[:1000]

        if any_ok:
            event.status = EventStatus.sent
            event.sent_at = datetime.now(timezone.utc)
            sent += 1
        elif attempted:
            event.status = EventStatus.failed
            failed += 1
        else:
            # Ningún destino configurado: se queda EN COLA hasta tener credenciales.
            event.status = EventStatus.queued
            skipped += 1

    db.commit()
    return {"sent": sent, "failed": failed, "skipped": skipped}
