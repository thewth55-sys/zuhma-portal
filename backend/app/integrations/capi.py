"""Meta Conversions API (server-side).

Envía el evento de conversión a Meta con el MISMO event_id del lead (para deduplicar
contra el pixel del navegador) y PII hasheada con SHA-256. Devuelve (ok, detalle).
"""

from __future__ import annotations

import hashlib
import re
import time

import httpx

from app.config import get_settings
from app.models import ConversionConfig, Lead, LeadEvent


def send_test(config: ConversionConfig) -> tuple[bool, str]:
    """Envía un evento de prueba y devuelve la respuesta cruda de Meta (diagnóstico)."""
    s = get_settings()
    url = f"https://graph.facebook.com/{s.meta_graph_version}/{config.meta_pixel_id}/events"
    payload: dict = {
        "data": [{
            "event_name": "Lead",
            "event_time": int(time.time()),
            "event_id": f"test-{int(time.time())}",
            "action_source": "system_generated",
            "user_data": {"em": [hashlib.sha256(b"test@zuhma.online").hexdigest()]},
        }],
        "access_token": config.meta_capi_token,
    }
    if config.meta_test_event_code:
        payload["test_event_code"] = config.meta_test_event_code
    try:
        resp = httpx.post(url, json=payload, timeout=15.0)
    except httpx.HTTPError as exc:
        return False, f"Error de red: {exc}"
    return (resp.status_code < 400), f"{resp.status_code}: {resp.text[:500]}"


def _sha256(value: str | None) -> str | None:
    if not value:
        return None
    return hashlib.sha256(value.strip().lower().encode()).hexdigest()


def _phone_hash(phone: str | None) -> str | None:
    if not phone:
        return None
    digits = re.sub(r"\D", "", phone)
    return hashlib.sha256(digits.encode()).hexdigest() if digits else None


def send(config: ConversionConfig, lead: Lead, event: LeadEvent) -> tuple[bool, str]:
    s = get_settings()
    url = f"https://graph.facebook.com/{s.meta_graph_version}/{config.meta_pixel_id}/events"

    user_data: dict = {}
    if em := _sha256(lead.email):
        user_data["em"] = [em]
    if ph := _phone_hash(lead.phone):
        user_data["ph"] = [ph]
    if lead.fbc:
        user_data["fbc"] = lead.fbc
    if lead.fbp:
        user_data["fbp"] = lead.fbp
    if not user_data:
        return False, "Sin datos de usuario para hacer match (email/teléfono/fbc)."

    payload: dict = {
        "data": [{
            "event_name": event.event_name,
            "event_time": int(time.time()),
            "event_id": event.event_id,           # dedup contra el pixel
            "action_source": "system_generated",
            "user_data": user_data,
            "custom_data": {"lead_id": lead.lead_id, "affinity": lead.propensity_score or 0},
        }],
        "access_token": config.meta_capi_token,
    }
    if config.meta_test_event_code:
        payload["test_event_code"] = config.meta_test_event_code

    try:
        resp = httpx.post(url, json=payload, timeout=15.0)
    except httpx.HTTPError as exc:
        return False, f"Error de red: {exc}"
    return (resp.status_code < 400), f"{resp.status_code}: {resp.text[:300]}"
