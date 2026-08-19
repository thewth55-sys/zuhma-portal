"""Envío de correos vía Resend (API HTTP). Secreto solo en el backend.

Si Resend no está configurado, devuelve (False, motivo) sin romper el flujo — el
llamador puede caer al plan B (mostrar el enlace al admin para enviarlo manual).
"""

from __future__ import annotations

import html as _html

import httpx

from app.config import get_settings


def send_email(to: str, subject: str, html_body: str) -> tuple[bool, str]:
    s = get_settings()
    if not (s.resend_api_key and s.resend_from):
        return False, "Resend no configurado (RESEND_API_KEY / RESEND_FROM)."
    payload: dict = {"from": s.resend_from, "to": [to], "subject": subject, "html": html_body}
    if s.resend_reply_to:
        payload["reply_to"] = [s.resend_reply_to]
    try:
        resp = httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {s.resend_api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=15.0,
        )
    except httpx.HTTPError as exc:
        return False, f"Error de red: {exc}"
    return (resp.status_code < 400), f"{resp.status_code}: {resp.text[:300]}"


# --- Plantillas -------------------------------------------------------------

_BASE = """<!doctype html><html><body style="margin:0;background:#f6f6fb;padding:32px 0;
font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#16151d">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center">
<table role="presentation" width="520" cellpadding="0" cellspacing="0"
style="background:#fff;border:1px solid #e9e8f0;border-radius:16px;overflow:hidden">
<tr><td style="background:linear-gradient(120deg,#f26152,#f7902e);padding:22px 26px;color:#fff;
font-size:20px;font-weight:800;letter-spacing:-.02em">zühma<span style="color:#ffe1c2">+</span></td></tr>
<tr><td style="padding:26px">{body}</td></tr>
<tr><td style="padding:16px 26px;border-top:1px solid #e9e8f0;color:#9997a8;font-size:12px">
Zuhma · Portal de clientes</td></tr>
</table></td></tr></table></body></html>"""


def _button(url: str, label: str) -> str:
    return (
        f'<a href="{_html.escape(url)}" style="display:inline-block;background:#f26152;color:#fff;'
        f'text-decoration:none;font-weight:700;padding:12px 22px;border-radius:10px;font-size:14px">'
        f"{_html.escape(label)}</a>"
    )


def otp_email(code: str) -> tuple[str, str]:
    """Devuelve (asunto, html) del código de verificación (2FA)."""
    subject = f"Tu código de acceso: {code} · zühma+"
    body = f"""
    <h1 style="font-size:20px;margin:0 0 8px">Código de verificación</h1>
    <p style="color:#6b6a7b;font-size:14px;line-height:1.6;margin:0 0 18px">
      Usa este código para completar tu inicio de sesión. Vence en 10 minutos.
    </p>
    <div style="font-size:34px;font-weight:800;letter-spacing:8px;color:#f26152;
      background:#fdece6;border-radius:12px;padding:16px;text-align:center">{code}</div>
    <p style="color:#9997a8;font-size:12px;line-height:1.6;margin:18px 0 0">
      Si no intentaste iniciar sesión, ignora este correo.
    </p>
    """
    return subject, _BASE.format(body=body)


def new_lead_email(client_name: str, lead) -> tuple[str, str]:
    """Aviso al equipo interno: ingresó un lead nuevo de un cliente."""
    subject = f"Nuevo lead · {client_name} · zühma+"
    name = _html.escape(str(getattr(lead, "contact_name", "") or "Lead"))
    channel = _html.escape(str(getattr(lead, "channel", "") or "Orgánico"))
    phone = _html.escape(str(getattr(lead, "phone", "") or "—"))
    mail = _html.escape(str(getattr(lead, "email", "") or "—"))
    code = _html.escape(str(getattr(lead, "lead_id", "") or ""))
    portal = (get_settings().portal_base_url or "").rstrip("/")
    button = _button(portal, "Abrir el portal") if portal else ""
    body = f"""
    <h1 style="font-size:20px;margin:0 0 8px">Nuevo lead de {_html.escape(client_name)}</h1>
    <p style="color:#6b6a7b;font-size:14px;line-height:1.6;margin:0 0 16px">
      Ingresó un lead a la cuenta. Ábrelo en el portal para atenderlo y calificarlo.
    </p>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="font-size:14px;margin:0 0 18px">
      <tr><td style="padding:6px 0;color:#9997a8;width:120px">Contacto</td><td style="padding:6px 0;font-weight:700">{name}</td></tr>
      <tr><td style="padding:6px 0;color:#9997a8">Canal</td><td style="padding:6px 0">{channel}</td></tr>
      <tr><td style="padding:6px 0;color:#9997a8">Teléfono</td><td style="padding:6px 0">{phone}</td></tr>
      <tr><td style="padding:6px 0;color:#9997a8">Correo</td><td style="padding:6px 0">{mail}</td></tr>
      <tr><td style="padding:6px 0;color:#9997a8">Lead ID</td><td style="padding:6px 0;font-family:monospace">{code}</td></tr>
    </table>
    {f'<p style="margin:0 0 6px">{button}</p>' if button else ''}
    <p style="color:#9997a8;font-size:12px;line-height:1.6;margin:14px 0 0">
      ¿Demasiados avisos de esta cuenta? Silénciala en el portal: Clientes → (cliente) → Alertas de leads.
    </p>
    """
    return subject, _BASE.format(body=body)


def reset_email(action_link: str) -> tuple[str, str]:
    """Devuelve (asunto, html) del restablecimiento de contraseña."""
    subject = "Restablece tu contraseña · zühma+"
    body = f"""
    <h1 style="font-size:20px;margin:0 0 8px">Restablecer contraseña</h1>
    <p style="color:#6b6a7b;font-size:14px;line-height:1.6;margin:0 0 20px">
      Un administrador solicitó restablecer tu contraseña del portal. Haz clic en el botón
      para definir una nueva. El enlace vence en 1 hora.
    </p>
    <p style="margin:0 0 22px">{_button(action_link, "Definir nueva contraseña")}</p>
    <p style="color:#9997a8;font-size:12px;line-height:1.6;margin:0">
      Si el botón no funciona, copia y pega este enlace en tu navegador:<br>
      <span style="color:#6b6a7b;word-break:break-all">{_html.escape(action_link)}</span>
    </p>
    <p style="color:#9997a8;font-size:12px;line-height:1.6;margin:14px 0 0">
      Si no esperabas este correo, ignóralo: tu contraseña actual seguirá funcionando.
    </p>
    """
    return subject, _BASE.format(body=body)


def invite_email(client_name: str, action_link: str) -> tuple[str, str]:
    """Devuelve (asunto, html) de la invitación al portal."""
    subject = f"Te invitaron al portal de {client_name} · zühma+"
    body = f"""
    <h1 style="font-size:20px;margin:0 0 8px">Bienvenido al portal de Zuhma</h1>
    <p style="color:#6b6a7b;font-size:14px;line-height:1.6;margin:0 0 20px">
      Se creó tu acceso al portal de <b>{_html.escape(client_name)}</b>. Haz clic en el botón para
      activar tu cuenta y definir tu contraseña.
    </p>
    <p style="margin:0 0 22px">{_button(action_link, "Activar mi acceso")}</p>
    <p style="color:#9997a8;font-size:12px;line-height:1.6;margin:0">
      Si el botón no funciona, copia y pega este enlace en tu navegador:<br>
      <span style="color:#6b6a7b;word-break:break-all">{_html.escape(action_link)}</span>
    </p>
    """
    return subject, _BASE.format(body=body)
