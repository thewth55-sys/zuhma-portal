"""Admin API de Supabase (GoTrue) — invitar/crear usuarios.

Usa el service_role (SOLO backend). `invite_user` crea el usuario en Supabase y
devuelve un enlace de invitación (action_link) para que acepte y ponga su contraseña.
No depende del SMTP de Supabase: devolvemos el enlace y el portal decide cómo enviarlo
(mostrarlo al admin o mandarlo por correo propio).
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.config import get_settings


class SupabaseAdminError(RuntimeError):
    pass


@dataclass
class InvitedUser:
    user_id: str
    email: str
    action_link: str | None


def _headers(key: str) -> dict:
    return {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def invite_user(email: str, full_name: str | None = None) -> InvitedUser:
    s = get_settings()
    if not (s.supabase_url and s.supabase_service_role_key):
        raise SupabaseAdminError(
            "Falta SUPABASE_SERVICE_ROLE_KEY (o SUPABASE_URL) en el backend para invitar usuarios."
        )
    url = f"{s.supabase_url.rstrip('/')}/auth/v1/admin/generate_link"
    payload: dict = {"type": "invite", "email": email, "data": {"full_name": full_name} if full_name else {}}
    # Redirige al portal (no al Site URL por defecto de Supabase). Debe estar en la
    # allow-list de Redirect URLs del proyecto Supabase.
    if s.portal_base_url:
        payload["redirect_to"] = s.portal_base_url.rstrip("/")
    try:
        resp = httpx.post(url, headers=_headers(s.supabase_service_role_key), json=payload, timeout=15.0)
    except httpx.HTTPError as exc:
        raise SupabaseAdminError(f"No se pudo contactar a Supabase: {exc}") from exc

    if resp.status_code >= 400:
        detail = resp.text
        if "already been registered" in detail or "email_exists" in detail or resp.status_code == 422:
            raise SupabaseAdminError("Ya existe un usuario de Supabase con ese correo.")
        raise SupabaseAdminError(f"Supabase rechazó la invitación ({resp.status_code}): {detail}")

    data = resp.json()
    # GoTrue devuelve los campos del usuario en el nivel superior + action_link.
    user_id = data.get("id") or (data.get("user") or {}).get("id")
    action_link = data.get("action_link") or (data.get("properties") or {}).get("action_link")
    if not user_id:
        raise SupabaseAdminError("Supabase no devolvió el id del usuario invitado.")
    return InvitedUser(user_id=str(user_id), email=email, action_link=action_link)
