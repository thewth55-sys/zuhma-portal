"""Repositorio del Lead Hub — persistente (Postgres) y ACOTADO POR TENANT.

Toda operación filtra por tenant_id: un lead de otro cliente jamás es alcanzable.
Aquí se centraliza la medición: al calificar un lead (status=potential) se genera el
evento de conversión (por ahora 'queued' hasta que el motor CAPI/Google tenga
credenciales), se calcula la propensidad y se registra la actividad.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.leadhub import scoring
from app.models import Lead, LeadActivity, LeadConfig, LeadEvent, LeadStatus, Tenant


def _new_lead_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"LZ-{stamp}-{secrets.token_hex(3).upper()}"


def _minutes_in_inbox(created_at: datetime) -> int:
    if created_at is None:
        return 0
    now = datetime.now(timezone.utc)
    ref = created_at if created_at.tzinfo else created_at.replace(tzinfo=timezone.utc)
    return max(0, int((now - ref).total_seconds() // 60))


# Umbral (min) para marcar un lead pendiente como "vencido" en la bandeja.
_OVERDUE_MIN = 24 * 60


class LeadRepository:
    def __init__(self, db: Session, tenant: Tenant):
        self.db = db
        self.tenant = tenant

    # --- Config del cuestionario/scoring por cliente --- #
    def get_config(self) -> dict:
        row = self.db.scalar(select(LeadConfig).where(LeadConfig.tenant_id == self.tenant.id))
        return row.config if row and row.config else scoring.get_config_for(self.tenant.slug)

    def _score(self, answers: dict) -> tuple[int, str]:
        return scoring.evaluate(self.get_config(), answers or {})

    # --- Serialización --- #
    def _card(self, lead: Lead) -> dict:
        mins = _minutes_in_inbox(lead.created_at)
        return {
            "id": lead.lead_id,
            "name": lead.contact_name,
            "affinity": lead.propensity_score,
            "band": lead.propensity_band,
            "channel": lead.channel,
            "status": lead.status.value,
            "owner": lead.owner,
            "released": lead.released,
            "minutes_in_inbox": mins,
            "overdue": lead.status == LeadStatus.pending and mins >= _OVERDUE_MIN,
            "description": lead.description or "",
            "contacts": [c for c in (
                {"kind": "phone", "value": lead.phone} if lead.phone else None,
                {"kind": "mail", "value": lead.email} if lead.email else None,
            ) if c],
        }

    def _detail(self, lead: Lead) -> dict:
        card = self._card(lead)
        card.update({
            "cargo": lead.cargo,
            "company_name": lead.company_name,
            "company_size": lead.company_size,
            "website": lead.website,
            "session_date": lead.session_date.isoformat() if lead.session_date else None,
            "answers": lead.answers or {},
            "propensity_score": lead.propensity_score,
            "propensity_band": lead.propensity_band,
            "attribution": {
                "gclid": lead.gclid, "fbclid": lead.fbclid, "fbc": lead.fbc, "fbp": lead.fbp,
                "utm_source": lead.utm_source, "utm_medium": lead.utm_medium, "utm_campaign": lead.utm_campaign,
            },
            "events": [
                {"event": e.event_name, "destination": e.destination, "status": e.status.value,
                 "event_id": e.event_id, "value": e.value,
                 "sent_at": e.sent_at.isoformat() if e.sent_at else None}
                for e in sorted(lead.events, key=lambda x: x.id)
            ],
            "activity": [
                {"kind": a.kind, "text": a.text, "at": a.created_at.isoformat() if a.created_at else None}
                for a in sorted(lead.activities, key=lambda x: x.id, reverse=True)
            ],
        })
        return card

    # --- Consultas --- #
    # admin_view=False → vista del CLIENTE: solo leads liberados (released=True).
    # admin_view=True  → vista del ADMIN: todos, calificados o no, liberados o no.
    def _scope(self, admin_view: bool):
        conds = [Lead.tenant_id == self.tenant.id]
        if not admin_view:
            conds.append(Lead.released.is_(True))
        return conds

    def kpis(self, admin_view: bool = False) -> dict:
        base = select(func.count()).select_from(Lead).where(*self._scope(admin_view))
        pending = self.db.scalar(base.where(Lead.status == LeadStatus.pending)) or 0
        qualified = self.db.scalar(base.where(Lead.status == LeadStatus.potential)) or 0
        total = self.db.scalar(base) or 0
        return {
            "pending": pending,
            "avg_response_hours": 8.0,  # placeholder hasta medir tiempos reales de atención
            "qualified_month": qualified,
            "answered_under_24h_pct": 0 if not total else round(100 * (total - pending) / total),
        }

    def list_leads(self, status: str | None = None, admin_view: bool = False) -> dict:
        stmt = select(Lead).where(*self._scope(admin_view)).order_by(Lead.created_at.desc())
        leads = list(self.db.scalars(stmt))
        counts = {s.value: sum(1 for x in leads if x.status == s) for s in LeadStatus}
        counts["all"] = len(leads)
        counts["released"] = sum(1 for x in leads if x.released)
        counts["unreleased"] = sum(1 for x in leads if not x.released)
        if status and status != "all":
            leads = [x for x in leads if x.status.value == status]
        return {"leads": [self._card(x) for x in leads], "counts": counts, "lead_mode": self.tenant.lead_mode}

    def get(self, lead_id: str, admin_view: bool = False) -> dict | None:
        lead = self.db.scalar(
            select(Lead)
            .where(*self._scope(admin_view), Lead.lead_id == lead_id)
            .options(selectinload(Lead.events), selectinload(Lead.activities))
        )
        return self._detail(lead) if lead else None

    def release(self, lead_id: str, released: bool = True) -> dict | None:
        lead = self.db.scalar(select(Lead).where(Lead.tenant_id == self.tenant.id, Lead.lead_id == lead_id))
        if lead is None:
            return None
        lead.released = released
        lead.activities.append(LeadActivity(kind="stage", text="Liberado al cliente." if released else "Retirado del cliente."))
        self.db.commit()
        return self.get(lead_id, admin_view=True)

    # --- Mutaciones --- #
    def create(self, payload: dict) -> dict:
        answers = payload.get("answers") or {}
        score, band = self._score(answers)
        # Liberación según el modelo del cliente: client_managed nace liberado;
        # agency_managed nace SIN liberar (el admin lo suelta al calificar).
        released = payload.get("released")
        if released is None:
            released = self.tenant.lead_mode != "agency_managed"
        lead = Lead(
            tenant_id=self.tenant.id,
            lead_id=_new_lead_id(),
            released=released,
            contact_name=payload["contact_name"],
            cargo=payload.get("cargo"),
            email=payload.get("email"),
            phone=payload.get("phone"),
            company_name=payload.get("company_name"),
            company_size=payload.get("company_size"),
            website=payload.get("website"),
            channel=payload.get("channel") or "Orgánico",
            owner=payload.get("owner") or "Sin dueño",
            description=payload.get("description"),
            answers=answers,
            propensity_score=score,
            propensity_band=band,
            gclid=payload.get("gclid"), fbclid=payload.get("fbclid"),
            fbc=payload.get("fbc"), fbp=payload.get("fbp"),
            utm_source=payload.get("utm_source"), utm_medium=payload.get("utm_medium"),
            utm_campaign=payload.get("utm_campaign"),
        )
        self.db.add(lead)
        self.db.flush()
        lead.activities.append(LeadActivity(kind="created", text=f"Lead creado por {payload.get('channel') or 'alta manual'}."))
        # Evento base 'Lead' (queued) — el motor CAPI/Google lo enviará cuando haya credenciales.
        lead.events.append(LeadEvent(event_name="Lead", destination="both", event_id=lead.lead_id))
        self.db.commit()
        self.db.refresh(lead)
        # admin_view=True: devuelve el lead recién creado aunque nazca sin liberar (agency).
        return self.get(lead.lead_id, admin_view=True)  # type: ignore[return-value]

    def update(self, lead_id: str, payload: dict) -> dict | None:
        lead = self.db.scalar(select(Lead).where(Lead.tenant_id == self.tenant.id, Lead.lead_id == lead_id))
        if lead is None:
            return None
        for field in ("contact_name", "cargo", "email", "phone", "company_name", "company_size",
                      "website", "channel", "owner", "description"):
            if field in payload and payload[field] is not None:
                setattr(lead, field, payload[field])
        if "answers" in payload:
            lead.answers = payload["answers"] or {}
            lead.propensity_score, lead.propensity_band = self._score(lead.answers)
            lead.activities.append(LeadActivity(kind="note", text=f"Calificación recalculada: {lead.propensity_score} ({lead.propensity_band})."))
        self.db.commit()
        return self.get(lead_id)

    def add_comment(self, lead_id: str, text: str, author: str) -> dict | None:
        lead = self.db.scalar(select(Lead).where(Lead.tenant_id == self.tenant.id, Lead.lead_id == lead_id))
        if lead is None:
            return None
        lead.activities.append(LeadActivity(kind="comment", text=f"{author}: {text}"))
        self.db.commit()
        return self.get(lead_id)

    def set_status(self, lead_id: str, status: str) -> dict | None:
        try:
            new = LeadStatus(status)
        except ValueError:
            raise KeyError(status)
        lead = self.db.scalar(
            select(Lead).where(Lead.tenant_id == self.tenant.id, Lead.lead_id == lead_id)
            .options(selectinload(Lead.events))
        )
        if lead is None:
            return None
        lead.status = new
        lead.activities.append(LeadActivity(kind="stage", text=f"Estado → {new.value}."))
        # Disparo de conversión según la config (queued hasta tener credenciales del motor).
        cfg_event = self.get_config().get("stage_events", {}).get(new.value)
        if cfg_event and not any(e.event_name == cfg_event["event"] for e in lead.events):
            lead.events.append(LeadEvent(
                event_name=cfg_event["event"],
                destination=cfg_event.get("destination", "both"),
                event_id=lead.lead_id,
                value=cfg_event.get("value"),
            ))
            lead.activities.append(LeadActivity(kind="event", text=f"Evento {cfg_event['event']} en cola → {cfg_event.get('destination','both')}."))
        self.db.commit()
        return self.get(lead_id)
