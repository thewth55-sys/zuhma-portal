from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_tenant, get_current_user
from app.models import AppUser, LeadAlertMute, Notification, Tenant

router = APIRouter(prefix="/me", tags=["me"])


class MePatch(BaseModel):
    full_name: str | None = None


class MuteIn(BaseModel):
    muted: bool


@router.get("")
def me(user: AppUser = Depends(get_current_user)) -> dict:
    """Identidad del usuario autenticado y su rol."""
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.value,
        "tenant_id": user.tenant_id,
        "permissions": user.effective_permissions,
    }


@router.patch("")
def update_me(body: MePatch, user: AppUser = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """El propio usuario actualiza sus datos (nombre)."""
    if body.full_name is not None:
        user.full_name = body.full_name.strip() or None
        db.commit()
    return {"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role.value}


# ---------------- Notificaciones (campana) ---------------- #

@router.get("/notifications")
def list_notifications(limit: int = 20, user: AppUser = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    limit = max(1, min(limit, 50))
    rows = db.scalars(
        select(Notification).where(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc()).limit(limit)
    ).all()
    unread = db.scalar(
        select(func.count()).select_from(Notification)
        .where(Notification.user_id == user.id, Notification.read_at.is_(None))
    ) or 0
    items = [{
        "id": n.id, "kind": n.kind, "title": n.title, "body": n.body,
        "lead_code": n.lead_code, "tenant_id": n.tenant_id,
        "read": n.read_at is not None,
        "at": n.created_at.isoformat() if n.created_at else None,
    } for n in rows]
    return {"items": items, "unread": unread}


@router.post("/notifications/{notif_id}/read")
def read_notification(notif_id: int, user: AppUser = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    n = db.get(Notification, notif_id)
    if n is None or n.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notificación no encontrada.")
    if n.read_at is None:
        n.read_at = func.now()
        db.commit()
    return {"ok": True}


@router.post("/notifications/read-all")
def read_all_notifications(user: AppUser = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    db.query(Notification).filter(
        Notification.user_id == user.id, Notification.read_at.is_(None)
    ).update({Notification.read_at: func.now()}, synchronize_session=False)
    db.commit()
    return {"ok": True}


# ---------------- Preferencia de alertas por cliente (silenciar) ---------------- #

@router.get("/alerts/{client_id}")
def get_alert_pref(client_id: int, user: AppUser = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    muted = db.scalar(
        select(LeadAlertMute).where(LeadAlertMute.user_id == user.id, LeadAlertMute.tenant_id == client_id)
    )
    return {"tenant_id": client_id, "muted": muted is not None}


@router.put("/alerts/{client_id}")
def set_alert_pref(client_id: int, body: MuteIn, user: AppUser = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    row = db.scalar(
        select(LeadAlertMute).where(LeadAlertMute.user_id == user.id, LeadAlertMute.tenant_id == client_id)
    )
    if body.muted and row is None:
        db.add(LeadAlertMute(user_id=user.id, tenant_id=client_id))
        db.commit()
    elif not body.muted and row is not None:
        db.delete(row)
        db.commit()
    return {"tenant_id": client_id, "muted": body.muted}


@router.get("/tenant")
def my_tenant(tenant: Tenant = Depends(get_current_tenant)) -> dict:
    """El tenant activo (respeta suplantación 'ver como cliente')."""
    return {
        "id": tenant.id,
        "slug": tenant.slug,
        "name": tenant.name,
        "plan": tenant.plan_name,
        "status": tenant.status,
        "odoo_partner_id": tenant.odoo_partner_id,
        "brand_primary": tenant.brand_primary,
        "enabled_modules": tenant.enabled_modules,  # null = todos
    }
