"""Google Ads — Offline Conversion Upload (uploadClickConversions).

Sube la conversión con el gclid del lead. Requiere: OAuth (client id/secret + refresh
token), developer token y el conversion action id. Best-effort: si falta gclid o
credenciales, devuelve (False, motivo). El developer token necesita acceso aprobado por
Google para operar en cuentas reales.
"""

from __future__ import annotations

from datetime import datetime, timezone

import httpx

from app.models import ConversionConfig, Lead, LeadEvent

_API_VERSION = "v17"


def _access_token(config: ConversionConfig) -> str | None:
    try:
        resp = httpx.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": config.google_client_id,
                "client_secret": config.google_client_secret,
                "refresh_token": config.google_refresh_token,
                "grant_type": "refresh_token",
            },
            timeout=15.0,
        )
        if resp.status_code >= 400:
            return None
        return resp.json().get("access_token")
    except httpx.HTTPError:
        return None


def send(config: ConversionConfig, lead: Lead, event: LeadEvent) -> tuple[bool, str]:
    if not lead.gclid:
        return False, "El lead no tiene gclid (Google offline requiere gclid)."
    token = _access_token(config)
    if not token:
        return False, "No se pudo obtener el access token de Google (revisa OAuth)."

    cid = config.google_customer_id
    url = f"https://googleads.googleapis.com/{_API_VERSION}/customers/{cid}:uploadClickConversions"
    headers = {
        "Authorization": f"Bearer {token}",
        "developer-token": config.google_developer_token or "",
        "Content-Type": "application/json",
    }
    if config.google_login_customer_id:
        headers["login-customer-id"] = config.google_login_customer_id

    body = {
        "conversions": [{
            "gclid": lead.gclid,
            "conversionAction": f"customers/{cid}/conversionActions/{config.google_conversion_action_id}",
            "conversionDateTime": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S+00:00"),
            "conversionValue": float(event.value or 1),
            "currencyCode": "MXN",
        }],
        "partialFailure": True,
    }
    try:
        resp = httpx.post(url, headers=headers, json=body, timeout=20.0)
    except httpx.HTTPError as exc:
        return False, f"Error de red: {exc}"
    return (resp.status_code < 400), f"{resp.status_code}: {resp.text[:300]}"
