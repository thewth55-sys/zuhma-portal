"""Alertas de lead nuevo hacia el equipo interno asignado.

Al ingresar un lead (webhook Meta/WordPress/Chatwoot o alta manual), se avisa a los
usuarios internos ASIGNADOS al cliente (managed_client_ids = ese cliente o null=todos),
activos y que no lo hayan silenciado. Dos canales: campana en el portal (Notification)
y correo (Resend), ambos best-effort para no romper la creación del lead.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AppUser, LeadAlertMute, Notification, Tenant, UserRole


def assigned_internal_users(db: Session, tenant: Tenant) -> list[AppUser]:
    users = db.scalars(
        select(AppUser).where(
            AppUser.role.in_([UserRole.admin, UserRole.zuhma_member]),
            AppUser.active.is_(True),
        )
    ).all()
    out: list[AppUser] = []
    for u in users:
        ids = u.managed_client_ids
        if ids is None or tenant.id in ids:  # null = todos los clientes
            out.append(u)
    return out


def muted_user_ids(db: Session, tenant: Tenant) -> set[int]:
    return set(db.scalars(select(LeadAlertMute.user_id).where(LeadAlertMute.tenant_id == tenant.id)).all())


def notify_new_lead(db: Session, tenant: Tenant, lead) -> None:
    """Crea la campana y manda correo a los asignados no silenciados. No lanza."""
    recipients = assigned_internal_users(db, tenant)
    if not recipients:
        return
    muted = muted_user_ids(db, tenant)
    title = f"Nuevo lead · {tenant.name}"
    body = f"{lead.contact_name} — {lead.channel or 'Orgánico'}"

    emails: list[str] = []
    for u in recipients:
        if u.id in muted:
            continue
        db.add(Notification(
            user_id=u.id, tenant_id=tenant.id, kind="new_lead",
            title=title, body=body, lead_code=lead.lead_id,
        ))
        if u.email:
            emails.append(u.email)
    db.commit()

    if emails:
        from app.integrations import email as mailer
        subject, html_body = mailer.new_lead_email(tenant.name, lead)
        for addr in emails:
            try:
                mailer.send_email(addr, subject, html_body)
            except Exception:  # noqa: BLE001 — correo best-effort
                pass
