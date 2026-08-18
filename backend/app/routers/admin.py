"""Panel admin — gestión de clientes, servicios e invitaciones. Solo rol admin.

- Clientes (tenants): alta, edición, listado con nº de usuarios.
- Vincular cliente ↔ partner de Odoo (búsqueda sobre res.partner).
- Servicios/plan por cliente (plan_quota).
- Invitar usuarios: crea el usuario en Supabase (Admin API) y lo mapea al tenant como
  'client'. Devuelve el enlace de invitación para compartir.
"""

from __future__ import annotations

import re
import secrets
import unicodedata
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.deps import allowed_client_ids, require_admin, require_internal, require_permission
from app.integrations import meta as meta_api
from app.leadhub.repository import LeadRepository
from app.models import (
    ALL_PERMISSIONS,
    AppUser,
    ConversionConfig,
    EventStatus,
    ImpersonationAudit,
    Lead,
    LeadConfig,
    LeadEvent,
    LeadStatus,
    LoginOtp,
    MetaPage,
    MfaSession,
    PlanQuota,
    Tenant,
    UserRole,
)
from app.odoo import OdooError, get_odoo
from app.odoo.repositories import TenantOdooRepository
from app.routers.leads import CommentIn, LeadIn, LeadPatch, StatusIn
from app.security.supabase_admin import SupabaseAdminError, invite_user

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_internal)])

# Dependencias de permiso reutilizables (el rol admin las cumple todas).
_clients_perm = Depends(require_permission("manage_clients"))
_leads_perm = Depends(require_permission("manage_leads"))


def _slugify(name: str) -> str:
    norm = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", norm.lower()).strip("-")
    return slug or "cliente"


def _current_period() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


# ---------------- Clientes ---------------- #

class ClientIn(BaseModel):
    name: str
    odoo_partner_id: int | None = None
    plan_name: str | None = None


class ClientPatch(BaseModel):
    name: str | None = None
    plan_name: str | None = None
    status: str | None = None
    odoo_partner_id: int | None = None
    lead_mode: str | None = None
    enabled_modules: list[str] | None = None


def _client_dict(db: Session, t: Tenant) -> dict:
    users = db.scalar(select(func.count()).select_from(AppUser).where(AppUser.tenant_id == t.id)) or 0
    return {
        "id": t.id, "slug": t.slug, "name": t.name, "plan": t.plan_name,
        "status": t.status, "is_active": t.is_active, "lead_mode": t.lead_mode,
        "enabled_modules": t.enabled_modules, "odoo_partner_id": t.odoo_partner_id, "users": users,
    }


class EmailTestIn(BaseModel):
    to: str


@router.get("/email/config")
def email_config() -> dict:
    s = get_settings()
    return {"configured": bool(s.resend_api_key and s.resend_from), "from": s.resend_from or None}


@router.post("/email/test")
def email_test(body: EmailTestIn) -> dict:
    from app.integrations import email as mailer

    ok, detail = mailer.send_email(
        body.to, "Prueba de correo · zühma+",
        mailer._BASE.format(body="<p style='font-size:14px'>Correo de prueba desde el portal ✓</p>"),
    )
    return {"ok": ok, "detail": detail}


@router.get("/dashboard")
def dashboard(user: AppUser = Depends(require_internal), db: Session = Depends(get_db)) -> dict:
    """Vista general del negocio (acotado a los clientes que el usuario puede ver)."""
    stmt = select(Tenant).order_by(Tenant.name)
    allowed = allowed_client_ids(user)
    if allowed is not None:
        stmt = stmt.where(Tenant.id.in_(allowed or [0]))
    tenants = db.scalars(stmt).all()
    clients_active = sum(1 for t in tenants if t.is_active)

    def count(*where) -> int:
        return db.scalar(select(func.count()).select_from(Lead).where(*where)) or 0

    leads_total = count()
    leads_pending = count(Lead.status == LeadStatus.pending)
    leads_qualified = count(Lead.status == LeadStatus.potential)
    events_sent = db.scalar(
        select(func.count()).select_from(LeadEvent).where(LeadEvent.status == EventStatus.sent)
    ) or 0
    events_queued = db.scalar(
        select(func.count()).select_from(LeadEvent).where(LeadEvent.status == EventStatus.queued)
    ) or 0

    per_client = []
    for t in tenants:
        per_client.append({
            "id": t.id, "name": t.name, "plan": t.plan_name, "status": t.status,
            "lead_mode": t.lead_mode,
            "leads": count(Lead.tenant_id == t.id),
            "qualified": count(Lead.tenant_id == t.id, Lead.status == LeadStatus.potential),
            "users": db.scalar(select(func.count()).select_from(AppUser).where(AppUser.tenant_id == t.id)) or 0,
        })

    recent_rows = db.execute(
        select(Lead.lead_id, Lead.contact_name, Lead.channel, Lead.propensity_band, Lead.created_at, Tenant.name)
        .join(Tenant, Tenant.id == Lead.tenant_id)
        .order_by(Lead.created_at.desc()).limit(8)
    ).all()
    recent = [
        {"lead_id": r[0], "name": r[1], "channel": r[2], "band": r[3],
         "at": r[4].isoformat() if r[4] else None, "client": r[5]}
        for r in recent_rows
    ]

    return {
        "clients_total": len(tenants),
        "clients_active": clients_active,
        "leads_total": leads_total,
        "leads_pending": leads_pending,
        "leads_qualified": leads_qualified,
        "events_sent": events_sent,
        "events_queued": events_queued,
        "per_client": per_client,
        "recent": recent,
    }


@router.get("/clients")
def list_clients(user: AppUser = Depends(require_internal), db: Session = Depends(get_db)) -> list[dict]:
    stmt = select(Tenant).order_by(Tenant.name)
    allowed = allowed_client_ids(user)
    if allowed is not None:
        stmt = stmt.where(Tenant.id.in_(allowed or [0]))
    return [_client_dict(db, t) for t in db.scalars(stmt).all()]


@router.post("/clients", status_code=status.HTTP_201_CREATED)
def create_client(body: ClientIn, db: Session = Depends(get_db), _: AppUser = Depends(require_permission("manage_clients"))) -> dict:
    if not body.name.strip():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "El nombre es obligatorio.")
    slug = _slugify(body.name)
    # slug único
    base, i = slug, 2
    while db.scalar(select(Tenant).where(Tenant.slug == slug)):
        slug = f"{base}-{i}"
        i += 1
    if body.odoo_partner_id and db.scalar(select(Tenant).where(Tenant.odoo_partner_id == body.odoo_partner_id)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ese partner de Odoo ya está vinculado a otro cliente.")
    tenant = Tenant(
        slug=slug, name=body.name.strip(),
        odoo_partner_id=body.odoo_partner_id or 0,
        plan_name=body.plan_name, status="active", is_active=True,
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return _client_dict(db, tenant)


@router.patch("/clients/{client_id}")
def update_client(client_id: int, body: ClientPatch, db: Session = Depends(get_db), _: AppUser = Depends(require_permission("manage_clients"))) -> dict:
    tenant = db.get(Tenant, client_id)
    if tenant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente no encontrado.")
    if body.name is not None:
        tenant.name = body.name
    if body.plan_name is not None:
        tenant.plan_name = body.plan_name
    if body.status is not None:
        tenant.status = body.status
        tenant.is_active = body.status == "active"
    if body.odoo_partner_id is not None:
        tenant.odoo_partner_id = body.odoo_partner_id
    if body.lead_mode is not None:
        if body.lead_mode not in ("agency_managed", "client_managed"):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "lead_mode inválido.")
        tenant.lead_mode = body.lead_mode
    if body.enabled_modules is not None:
        tenant.enabled_modules = body.enabled_modules
    db.commit()
    return _client_dict(db, tenant)


# ---------------- Datos de Odoo por cliente (facturas, tareas) ---------------- #

def _odoo_repo(client_id: int, db: Session) -> TenantOdooRepository:
    tenant = db.get(Tenant, client_id)
    if tenant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente no encontrado.")
    if not tenant.odoo_partner_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Este cliente no tiene partner de Odoo vinculado.")
    return TenantOdooRepository(get_odoo(), tenant.odoo_partner_id)


@router.get("/clients/{client_id}/odoo/invoices")
def client_odoo_invoices(client_id: int, db: Session = Depends(get_db)) -> list[dict]:
    try:
        return _odoo_repo(client_id, db).list_invoices(limit=50)
    except OdooError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc))


@router.get("/clients/{client_id}/odoo/tasks")
def client_odoo_tasks(client_id: int, db: Session = Depends(get_db)) -> list[dict]:
    try:
        return _odoo_repo(client_id, db).list_recent_tasks(limit=50)
    except OdooError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc))


# ---------------- Equipo interno (require manage_team) ---------------- #

_team_perm = Depends(require_permission("manage_team"))


class TeamInviteIn(BaseModel):
    email: str
    full_name: str | None = None
    role: str = "zuhma_member"       # zuhma_member | admin
    permissions: list[str] = []
    managed_client_ids: list[int] | None = None  # null = todos


class TeamPatchIn(BaseModel):
    role: str | None = None
    permissions: list[str] | None = None
    managed_client_ids: list[int] | None = None
    active: bool | None = None


def _member_dict(u: AppUser) -> dict:
    return {
        "id": u.id, "email": u.email, "full_name": u.full_name, "role": u.role.value,
        "active": u.active, "permissions": u.effective_permissions,
        "managed_client_ids": u.managed_client_ids,
    }


@router.get("/team/permissions")
def team_permissions(_: AppUser = _team_perm) -> dict:
    return {"permissions": ALL_PERMISSIONS}


@router.get("/team/clients")
def team_clients(db: Session = Depends(get_db), _: AppUser = _team_perm) -> list[dict]:
    """Lista simple de clientes para asignar (id + nombre)."""
    return [{"id": t.id, "name": t.name} for t in db.scalars(select(Tenant).order_by(Tenant.name)).all()]


@router.get("/team")
def list_team(db: Session = Depends(get_db), _: AppUser = _team_perm) -> list[dict]:
    members = db.scalars(
        select(AppUser).where(AppUser.role.in_([UserRole.admin, UserRole.zuhma_member])).order_by(AppUser.email)
    ).all()
    return [_member_dict(u) for u in members]


@router.post("/team/invite", status_code=status.HTTP_201_CREATED)
def invite_member(body: TeamInviteIn, db: Session = Depends(get_db), _: AppUser = _team_perm) -> dict:
    email = body.email.strip().lower()
    if not email:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "El correo es obligatorio.")
    role = UserRole.admin if body.role == "admin" else UserRole.zuhma_member

    existing = db.scalar(select(AppUser).where(AppUser.email == email))
    if existing:
        existing.role = role
        existing.permissions = body.permissions
        existing.managed_client_ids = body.managed_client_ids
        existing.active = True
        existing.tenant_id = None
        db.commit()
        return {"status": "updated", "member": _member_dict(existing), "action_link": None, "email_sent": False}

    try:
        invited = invite_user(email, body.full_name)
    except SupabaseAdminError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))

    user = AppUser(
        supabase_user_id=invited.user_id, email=email, full_name=body.full_name,
        role=role, permissions=body.permissions, managed_client_ids=body.managed_client_ids, active=True,
    )
    db.add(user)
    db.commit()

    email_sent = False
    if invited.action_link:
        from app.integrations import email as mailer

        subject, html_body = mailer.invite_email("Equipo Zuhma", invited.action_link)
        email_sent, _detail = mailer.send_email(email, subject, html_body)

    return {"status": "invited", "member": _member_dict(user), "action_link": invited.action_link, "email_sent": email_sent}


@router.patch("/team/{member_id}")
def update_member(member_id: int, body: TeamPatchIn, db: Session = Depends(get_db), actor: AppUser = _team_perm) -> dict:
    u = db.get(AppUser, member_id)
    if u is None or u.role == UserRole.client:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Miembro no encontrado.")
    if body.role is not None:
        u.role = UserRole.admin if body.role == "admin" else UserRole.zuhma_member
    if body.permissions is not None:
        u.permissions = body.permissions
    if body.managed_client_ids is not None:
        u.managed_client_ids = body.managed_client_ids
    if body.active is not None:
        if u.id == actor.id and not body.active:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "No puedes desactivarte a ti mismo.")
        u.active = body.active
    db.commit()
    return _member_dict(u)


@router.delete("/team/{member_id}")
def delete_member(member_id: int, actor: AppUser = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    """Elimina definitivamente a un miembro interno. Solo administradores."""
    u = db.get(AppUser, member_id)
    if u is None or u.role == UserRole.client:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Miembro no encontrado.")
    if u.id == actor.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No puedes eliminarte a ti mismo.")

    from app.security.supabase_admin import delete_user as sb_delete

    if u.supabase_user_id:
        sb_delete(u.supabase_user_id)  # best-effort: libera el correo en Supabase

    # Limpia dependencias antes de borrar (FKs).
    db.execute(delete(LoginOtp).where(LoginOtp.user_id == u.id))
    db.execute(delete(MfaSession).where(MfaSession.user_id == u.id))
    db.execute(delete(ImpersonationAudit).where(ImpersonationAudit.admin_user_id == u.id))
    db.delete(u)
    db.commit()
    return {"ok": True}


# ---------------- Partners de Odoo (para vincular) ---------------- #

@router.get("/odoo-partners")
def search_partners(q: str) -> list[dict]:
    if len(q.strip()) < 2:
        return []
    try:
        rows = get_odoo().search_read(
            "res.partner",
            ["|", ("name", "ilike", q), ("email", "ilike", q)],
            ["id", "name", "email", "is_company"],
            limit=12, order="is_company desc, name asc",
        )
    except OdooError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc))
    return rows


# ---------------- Usuarios / invitaciones ---------------- #

class InviteIn(BaseModel):
    email: str
    full_name: str | None = None


@router.get("/clients/{client_id}/users")
def list_users(client_id: int, db: Session = Depends(get_db)) -> list[dict]:
    users = db.scalars(select(AppUser).where(AppUser.tenant_id == client_id)).all()
    return [{"id": u.id, "email": u.email, "full_name": u.full_name, "role": u.role.value} for u in users]


@router.post("/clients/{client_id}/invite", status_code=status.HTTP_201_CREATED)
def invite(client_id: int, body: InviteIn, db: Session = Depends(get_db), _p: AppUser = _clients_perm) -> dict:
    tenant = db.get(Tenant, client_id)
    if tenant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente no encontrado.")
    email = body.email.strip().lower()
    if not email:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "El correo es obligatorio.")

    existing = db.scalar(select(AppUser).where(AppUser.email == email))
    if existing:
        # Ya existe en el portal: solo (re)asignar al cliente como client.
        existing.tenant_id = tenant.id
        if existing.role == UserRole.client:
            existing.tenant_id = tenant.id
        db.commit()
        return {"status": "reassigned", "message": "El usuario ya existía; se reasignó a este cliente.", "action_link": None}

    try:
        invited = invite_user(email, body.full_name)
    except SupabaseAdminError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))

    user = AppUser(
        supabase_user_id=invited.user_id, email=email, full_name=body.full_name,
        role=UserRole.client, tenant_id=tenant.id,
    )
    db.add(user)
    db.commit()

    # Envía la invitación por correo (Resend). Si no está configurado o falla, se
    # devuelve el action_link para que el admin lo comparta manualmente.
    email_sent, email_detail = False, None
    if invited.action_link:
        from app.integrations import email as mailer

        subject, html_body = mailer.invite_email(tenant.name, invited.action_link)
        email_sent, email_detail = mailer.send_email(email, subject, html_body)

    return {
        "status": "invited", "email": email, "action_link": invited.action_link,
        "email_sent": email_sent, "email_detail": email_detail,
    }


# ---------------- Servicios / plan ---------------- #

class ServiceIn(BaseModel):
    metric: str
    label: str
    total: int = 0
    used: int = 0
    period: str | None = None


@router.get("/clients/{client_id}/services")
def list_services(client_id: int, db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(
        select(PlanQuota).where(PlanQuota.tenant_id == client_id).order_by(PlanQuota.period.desc(), PlanQuota.id)
    ).all()
    return [{"id": q.id, "metric": q.metric, "label": q.label, "used": q.used, "total": q.total, "period": q.period} for q in rows]


@router.post("/clients/{client_id}/services", status_code=status.HTTP_201_CREATED)
def add_service(client_id: int, body: ServiceIn, db: Session = Depends(get_db)) -> dict:
    if db.get(Tenant, client_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente no encontrado.")
    q = PlanQuota(
        tenant_id=client_id, period=body.period or _current_period(),
        metric=body.metric.strip() or "servicio", label=body.label.strip() or body.metric,
        used=body.used, total=body.total,
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return {"id": q.id, "metric": q.metric, "label": q.label, "used": q.used, "total": q.total, "period": q.period}


# ---------------- Leads por cliente (admin ve TODO) ---------------- #

class ReleaseIn(BaseModel):
    released: bool = True


def _lead_repo(client_id: int, db: Session) -> LeadRepository:
    tenant = db.get(Tenant, client_id)
    if tenant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente no encontrado.")
    return LeadRepository(db, tenant)


@router.get("/clients/{client_id}/leads/kpis")
def admin_lead_kpis(client_id: int, db: Session = Depends(get_db)) -> dict:
    return _lead_repo(client_id, db).kpis(admin_view=True)


@router.get("/clients/{client_id}/lead-config")
def admin_lead_config(client_id: int, db: Session = Depends(get_db)) -> dict:
    return _lead_repo(client_id, db).get_config()


@router.put("/clients/{client_id}/lead-config")
def save_lead_config(client_id: int, body: dict, db: Session = Depends(get_db)) -> dict:
    if db.get(Tenant, client_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente no encontrado.")
    row = db.scalar(select(LeadConfig).where(LeadConfig.tenant_id == client_id))
    if row is None:
        row = LeadConfig(tenant_id=client_id, config=body)
        db.add(row)
    else:
        row.config = body
    db.commit()
    return body


@router.get("/clients/{client_id}/leads")
def admin_list_leads(client_id: int, status_filter: str | None = None, db: Session = Depends(get_db)) -> dict:
    return _lead_repo(client_id, db).list_leads(status_filter, admin_view=True)


@router.get("/clients/{client_id}/leads/{lead_id}")
def admin_get_lead(client_id: int, lead_id: str, db: Session = Depends(get_db)) -> dict:
    detail = _lead_repo(client_id, db).get(lead_id, admin_view=True)
    if detail is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead no encontrado.")
    return detail


@router.post("/clients/{client_id}/leads", status_code=status.HTTP_201_CREATED)
def admin_create_lead(client_id: int, body: LeadIn, db: Session = Depends(get_db), _p: AppUser = _leads_perm) -> dict:
    if not body.contact_name.strip():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "El nombre del contacto es obligatorio.")
    return _lead_repo(client_id, db).create(body.model_dump())


@router.patch("/clients/{client_id}/leads/{lead_id}")
def admin_update_lead(client_id: int, lead_id: str, body: LeadPatch, db: Session = Depends(get_db)) -> dict:
    updated = _lead_repo(client_id, db).update(lead_id, body.model_dump(exclude_none=True))
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead no encontrado.")
    return updated


@router.post("/clients/{client_id}/leads/{lead_id}/status")
def admin_set_status(client_id: int, lead_id: str, body: StatusIn, db: Session = Depends(get_db), _p: AppUser = _leads_perm) -> dict:
    repo = _lead_repo(client_id, db)
    try:
        updated = repo.set_status(lead_id, body.status)
    except KeyError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Estado inválido: {body.status}")
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead no encontrado.")
    from app.leadhub import conversions
    conversions.flush_lead(db, repo.tenant, lead_id)
    return repo.get(lead_id, admin_view=True) or updated


@router.post("/clients/{client_id}/leads/{lead_id}/flush")
def admin_flush_events(client_id: int, lead_id: str, db: Session = Depends(get_db)) -> dict:
    """Reintenta enviar los eventos de conversión en cola del lead."""
    repo = _lead_repo(client_id, db)
    from app.leadhub import conversions
    summary = conversions.flush_lead(db, repo.tenant, lead_id)
    detail = repo.get(lead_id, admin_view=True)
    if detail is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead no encontrado.")
    return {"summary": summary, "lead": detail}


@router.post("/clients/{client_id}/leads/{lead_id}/release")
def admin_release_lead(client_id: int, lead_id: str, body: ReleaseIn, db: Session = Depends(get_db), _p: AppUser = _leads_perm) -> dict:
    updated = _lead_repo(client_id, db).release(lead_id, body.released)
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead no encontrado.")
    return updated


@router.post("/clients/{client_id}/leads/{lead_id}/comment")
def admin_comment_lead(client_id: int, lead_id: str, body: CommentIn, user: AppUser = Depends(require_internal), db: Session = Depends(get_db)) -> dict:
    updated = _lead_repo(client_id, db).add_comment(lead_id, body.text.strip(), user.full_name or user.email)
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead no encontrado.")
    return updated


# ---------------- Fuentes de leads (webhook de ingesta) ---------------- #

def _ensure_token(tenant: Tenant, db: Session) -> str:
    if not tenant.ingest_token:
        tenant.ingest_token = secrets.token_urlsafe(24)
        db.commit()
    return tenant.ingest_token


@router.get("/clients/{client_id}/ingest")
def get_ingest(client_id: int, db: Session = Depends(get_db)) -> dict:
    tenant = db.get(Tenant, client_id)
    if tenant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente no encontrado.")
    token = _ensure_token(tenant, db)
    return {"token": token, "path": f"/ingest/{token}/lead"}


@router.post("/clients/{client_id}/ingest/rotate")
def rotate_ingest(client_id: int, db: Session = Depends(get_db)) -> dict:
    tenant = db.get(Tenant, client_id)
    if tenant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente no encontrado.")
    tenant.ingest_token = secrets.token_urlsafe(24)
    db.commit()
    return {"token": tenant.ingest_token, "path": f"/ingest/{tenant.ingest_token}/lead"}


# ---------------- Meta Lead Ads (integración nativa) ---------------- #

class MetaPageIn(BaseModel):
    page_id: str
    page_name: str | None = None
    page_access_token: str


@router.get("/meta/config")
def meta_config() -> dict:
    """Datos para configurar el webhook en la App de Meta (Developers → Webhooks)."""
    s = get_settings()
    return {
        "callback_path": "/webhooks/meta",
        "verify_token_set": bool(s.meta_verify_token),
        "app_configured": bool(s.meta_app_id and s.meta_app_secret),
        "graph_version": s.meta_graph_version,
    }


class MetaAppIn(BaseModel):
    app_id: str
    app_secret: str
    verify_token: str


@router.get("/clients/{client_id}/meta-app")
def get_client_meta_app(client_id: int, db: Session = Depends(get_db)) -> dict:
    """Config de la App de Meta PROPIA del cliente (secret enmascarado)."""
    t = db.get(Tenant, client_id)
    if t is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente no encontrado.")
    configured = bool(t.meta_app_id and t.meta_app_secret)
    return {
        "configured": configured,
        "app_id": t.meta_app_id,
        "has_secret": bool(t.meta_app_secret),
        "verify_token": t.meta_verify_token,
        "webhook_path": f"/webhooks/meta/{t.meta_webhook_token}" if t.meta_webhook_token else None,
    }


@router.put("/clients/{client_id}/meta-app")
def set_client_meta_app(client_id: int, body: MetaAppIn, db: Session = Depends(get_db)) -> dict:
    t = db.get(Tenant, client_id)
    if t is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente no encontrado.")
    t.meta_app_id = body.app_id.strip()
    t.meta_app_secret = body.app_secret.strip()
    t.meta_verify_token = body.verify_token.strip()
    if not t.meta_webhook_token:
        t.meta_webhook_token = secrets.token_urlsafe(18)
    db.commit()
    return {"configured": True, "app_id": t.meta_app_id, "verify_token": t.meta_verify_token,
            "webhook_path": f"/webhooks/meta/{t.meta_webhook_token}"}


@router.delete("/clients/{client_id}/meta-app")
def clear_client_meta_app(client_id: int, db: Session = Depends(get_db)) -> dict:
    t = db.get(Tenant, client_id)
    if t is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente no encontrado.")
    t.meta_app_id = t.meta_app_secret = t.meta_verify_token = None
    db.commit()
    return {"ok": True}


class ConversionIn(BaseModel):
    meta_pixel_id: str | None = None
    meta_capi_token: str | None = None
    meta_test_event_code: str | None = None
    google_customer_id: str | None = None
    google_login_customer_id: str | None = None
    google_conversion_action_id: str | None = None
    google_developer_token: str | None = None
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_refresh_token: str | None = None


@router.get("/clients/{client_id}/conversion-config")
def get_conversion_config(client_id: int, db: Session = Depends(get_db)) -> dict:
    c = db.scalar(select(ConversionConfig).where(ConversionConfig.tenant_id == client_id))
    if c is None:
        return {"meta_ready": False, "google_ready": False, "meta_pixel_id": None, "meta_test_event_code": None,
                "has_meta_token": False, "google_customer_id": None, "google_login_customer_id": None,
                "google_conversion_action_id": None, "has_google_dev_token": False,
                "google_client_id": None, "has_google_secret": False, "has_google_refresh": False}
    return {
        "meta_ready": c.meta_ready, "google_ready": c.google_ready,
        "meta_pixel_id": c.meta_pixel_id, "meta_test_event_code": c.meta_test_event_code,
        "has_meta_token": bool(c.meta_capi_token),
        "google_customer_id": c.google_customer_id, "google_login_customer_id": c.google_login_customer_id,
        "google_conversion_action_id": c.google_conversion_action_id,
        "has_google_dev_token": bool(c.google_developer_token),
        "google_client_id": c.google_client_id,
        "has_google_secret": bool(c.google_client_secret), "has_google_refresh": bool(c.google_refresh_token),
    }


@router.put("/clients/{client_id}/conversion-config")
def set_conversion_config(client_id: int, body: ConversionIn, db: Session = Depends(get_db), _p: AppUser = _leads_perm) -> dict:
    if db.get(Tenant, client_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente no encontrado.")
    c = db.scalar(select(ConversionConfig).where(ConversionConfig.tenant_id == client_id))
    if c is None:
        c = ConversionConfig(tenant_id=client_id)
        db.add(c)
    # Solo actualiza los campos enviados (para no borrar secretos ya guardados).
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(c, field, value)
    db.commit()
    # Al quedar listo, reintenta automáticamente los eventos en cola del cliente.
    flushed = {"sent": 0, "failed": 0, "skipped": 0}
    if c.meta_ready or c.google_ready:
        from app.leadhub import conversions
        tenant = db.get(Tenant, client_id)
        if tenant is not None:
            flushed = conversions.flush_tenant_queued(db, tenant)
    return {"ok": True, "meta_ready": c.meta_ready, "google_ready": c.google_ready, "flushed": flushed}


@router.post("/clients/{client_id}/conversion-config/test-meta")
def test_meta_capi(client_id: int, db: Session = Depends(get_db)) -> dict:
    """Envía un evento de prueba a Meta CAPI y devuelve la respuesta cruda."""
    c = db.scalar(select(ConversionConfig).where(ConversionConfig.tenant_id == client_id))
    if c is None or not c.meta_ready:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Meta CAPI sin configurar para este cliente.")
    from app.integrations import capi

    ok, detail = capi.send_test(c)
    return {"ok": ok, "detail": detail, "test_event_code": c.meta_test_event_code}


@router.get("/clients/{client_id}/meta-pages")
def list_meta_pages(client_id: int, db: Session = Depends(get_db)) -> list[dict]:
    pages = db.scalars(select(MetaPage).where(MetaPage.tenant_id == client_id)).all()
    return [{"id": p.id, "page_id": p.page_id, "page_name": p.page_name, "is_active": p.is_active} for p in pages]


@router.post("/clients/{client_id}/meta-pages", status_code=status.HTTP_201_CREATED)
def connect_meta_page(client_id: int, body: MetaPageIn, db: Session = Depends(get_db), _p: AppUser = _leads_perm) -> dict:
    if db.get(Tenant, client_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente no encontrado.")
    if db.scalar(select(MetaPage).where(MetaPage.page_id == body.page_id)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Esa página ya está conectada.")
    page = MetaPage(
        tenant_id=client_id, page_id=body.page_id.strip(),
        page_name=body.page_name, page_access_token=body.page_access_token.strip(),
    )
    db.add(page)
    db.commit()
    # Suscribe la App al campo 'leadgen' de la página (best-effort; se reporta el resultado).
    sub = meta_api.subscribe_page(page.page_id, page.page_access_token)
    return {"id": page.id, "page_id": page.page_id, "subscribe": sub}


@router.delete("/clients/{client_id}/meta-pages/{page_pk}")
def disconnect_meta_page(client_id: int, page_pk: int, db: Session = Depends(get_db)) -> dict:
    page = db.get(MetaPage, page_pk)
    if page is None or page.tenant_id != client_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Página no encontrada.")
    page.is_active = False
    db.commit()
    return {"ok": True}
