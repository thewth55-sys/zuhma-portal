"""Panel admin — gestión de clientes, servicios e invitaciones. Solo rol admin.

- Clientes (tenants): alta, edición, listado con nº de usuarios.
- Vincular cliente ↔ partner de Odoo (búsqueda sobre res.partner).
- Servicios/plan por cliente (plan_quota).
- Invitar usuarios: crea el usuario en Supabase (Admin API) y lo mapea al tenant como
  'client'. Devuelve el enlace de invitación para compartir.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require_admin
from app.leadhub.repository import LeadRepository
from app.models import AppUser, LeadConfig, PlanQuota, Tenant, UserRole
from app.odoo import OdooError, get_odoo
from app.routers.leads import CommentIn, LeadIn, LeadPatch, StatusIn
from app.security.supabase_admin import SupabaseAdminError, invite_user

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


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


def _client_dict(db: Session, t: Tenant) -> dict:
    users = db.scalar(select(func.count()).select_from(AppUser).where(AppUser.tenant_id == t.id)) or 0
    return {
        "id": t.id, "slug": t.slug, "name": t.name, "plan": t.plan_name,
        "status": t.status, "is_active": t.is_active, "lead_mode": t.lead_mode,
        "odoo_partner_id": t.odoo_partner_id, "users": users,
    }


@router.get("/clients")
def list_clients(db: Session = Depends(get_db)) -> list[dict]:
    tenants = db.scalars(select(Tenant).order_by(Tenant.name)).all()
    return [_client_dict(db, t) for t in tenants]


@router.post("/clients", status_code=status.HTTP_201_CREATED)
def create_client(body: ClientIn, db: Session = Depends(get_db)) -> dict:
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
def update_client(client_id: int, body: ClientPatch, db: Session = Depends(get_db)) -> dict:
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
    db.commit()
    return _client_dict(db, tenant)


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
def invite(client_id: int, body: InviteIn, db: Session = Depends(get_db)) -> dict:
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
    return {"status": "invited", "email": email, "action_link": invited.action_link}


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
def admin_create_lead(client_id: int, body: LeadIn, db: Session = Depends(get_db)) -> dict:
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
def admin_set_status(client_id: int, lead_id: str, body: StatusIn, db: Session = Depends(get_db)) -> dict:
    try:
        updated = _lead_repo(client_id, db).set_status(lead_id, body.status)
    except KeyError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Estado inválido: {body.status}")
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead no encontrado.")
    return updated


@router.post("/clients/{client_id}/leads/{lead_id}/release")
def admin_release_lead(client_id: int, lead_id: str, body: ReleaseIn, db: Session = Depends(get_db)) -> dict:
    updated = _lead_repo(client_id, db).release(lead_id, body.released)
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead no encontrado.")
    return updated


@router.post("/clients/{client_id}/leads/{lead_id}/comment")
def admin_comment_lead(client_id: int, lead_id: str, body: CommentIn, user: AppUser = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    updated = _lead_repo(client_id, db).add_comment(lead_id, body.text.strip(), user.full_name or user.email)
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead no encontrado.")
    return updated
