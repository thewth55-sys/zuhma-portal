"""Integración nativa con Meta Lead Ads (Graph API).

Flujo: Meta envía un webhook 'leadgen' al recibir un lead → verificamos la firma con
el App Secret → leemos el lead por Graph API con el Page Access Token → lo mapeamos a
los campos del Lead Hub. Sin n8n de por medio.
"""

from __future__ import annotations

import hashlib
import hmac

import httpx

from app.config import get_settings

_STANDARD = {"full_name", "first_name", "last_name", "email", "phone_number", "company_name", "job_title"}
_LEAD_FIELDS = "field_data,ad_id,ad_name,adset_id,adset_name,campaign_id,campaign_name,form_id,created_time,platform"


def verify_signature(raw_body: bytes, signature_header: str | None, app_secret: str | None = None) -> bool:
    """Valida X-Hub-Signature-256 (HMAC-SHA256 del cuerpo crudo con el App Secret).

    `app_secret` explícito → App propia del cliente; si es None, usa el global de Zuhma.
    """
    secret = app_secret or get_settings().meta_app_secret
    if not secret or not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header.split("=", 1)[1])


def fetch_lead(leadgen_id: str, page_token: str) -> dict:
    s = get_settings()
    url = f"https://graph.facebook.com/{s.meta_graph_version}/{leadgen_id}"
    resp = httpx.get(url, params={"access_token": page_token, "fields": _LEAD_FIELDS}, timeout=15.0)
    resp.raise_for_status()
    return resp.json()


def subscribe_page(page_id: str, page_token: str) -> dict:
    """Suscribe la App al campo 'leadgen' de la página (para recibir sus webhooks)."""
    s = get_settings()
    url = f"https://graph.facebook.com/{s.meta_graph_version}/{page_id}/subscribed_apps"
    try:
        resp = httpx.post(url, params={"subscribed_fields": "leadgen", "access_token": page_token}, timeout=15.0)
        return {"ok": resp.status_code < 400, "status": resp.status_code, "detail": resp.text[:300]}
    except httpx.HTTPError as exc:
        return {"ok": False, "detail": str(exc)}


def _first(field_data: list, name: str) -> str | None:
    for f in field_data:
        if f.get("name") == name:
            vals = f.get("values") or []
            return vals[0] if vals else None
    return None


def map_lead_fields(graph_lead: dict) -> dict:
    """Graph lead → payload del Lead Hub (contacto + atribución + preguntas extra)."""
    field_data = graph_lead.get("field_data", []) or []
    name = _first(field_data, "full_name")
    if not name:
        name = " ".join(filter(None, [_first(field_data, "first_name"), _first(field_data, "last_name")])).strip()

    extras = {
        f["name"]: (f.get("values") or [None])[0]
        for f in field_data
        if f.get("name") not in _STANDARD
    }
    payload: dict = {
        "contact_name": name or "Lead de Meta",
        "email": _first(field_data, "email"),
        "phone": _first(field_data, "phone_number"),
        "company_name": _first(field_data, "company_name"),
        "cargo": _first(field_data, "job_title"),
        "channel": "Meta Ads",
        "source": f"meta:form:{graph_lead.get('form_id', '')}",
        "utm_source": "meta",
        "utm_campaign": graph_lead.get("campaign_name"),
        "answers": extras,
    }
    if extras:
        payload["description"] = " · ".join(f"{k}: {v}" for k, v in extras.items())
    return payload
