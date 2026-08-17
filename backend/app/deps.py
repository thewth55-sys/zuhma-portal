"""Dependencias FastAPI: autenticación, resolución de tenant y aislamiento.

Cadena de confianza:
  Authorization: Bearer <jwt Supabase>
      → verify_token()            (firma/exp/aud)
      → get_current_user()        (AppUser en la BD propia; auto-provisiona en 1er login)
      → get_current_tenant()      (el tenant que el usuario PUEDE ver)
      → get_tenant_repo()         (OdooClient acotado por partner_id del tenant)

Regla dura: el aislamiento se decide AQUÍ (backend), nunca en el frontend.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models import AppUser, ImpersonationAudit, Tenant, UserRole
from app.odoo import get_odoo
from app.odoo.repositories import TenantOdooRepository
from app.security.supabase_auth import AuthError, verify_token

settings = get_settings()


def _bearer(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Falta el header Authorization: Bearer <token>.")
    return authorization.split(" ", 1)[1].strip()


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> AppUser:
    token = _bearer(authorization)
    try:
        ident = verify_token(token)
    except AuthError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc

    user = db.scalar(select(AppUser).where(AppUser.supabase_user_id == ident.sub))
    if user is None:
        # Auto-provisión en el primer login. El rol se decide por lista de admins.
        role = UserRole.admin if ident.email in settings.admin_emails else UserRole.client
        user = AppUser(supabase_user_id=ident.sub, email=ident.email, role=role)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def _log_impersonation(db: Session, admin: AppUser, tenant: Tenant, ip: str | None) -> None:
    db.add(
        ImpersonationAudit(
            admin_user_id=admin.id,
            admin_email=admin.email,
            tenant_id=tenant.id,
            started_at=datetime.now(timezone.utc),
            ip=ip,
        )
    )
    db.commit()


def get_current_tenant(
    user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    x_impersonate_tenant: int | None = Header(default=None),
    x_forwarded_for: str | None = Header(default=None),
) -> Tenant:
    """Devuelve el tenant que el usuario tiene permitido ver.

    - client         → su propio tenant, y solo el suyo.
    - admin / zuhma_member → el suyo, o cualquiera vía cabecera `X-Impersonate-Tenant`
                       ("ver como cliente"), quedando AUDITADO.
    """
    # Suplantación (solo roles elevados) — auditada y explícita.
    if x_impersonate_tenant is not None:
        if user.role not in (UserRole.admin, UserRole.zuhma_member):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "No autorizado a ver como cliente.")
        tenant = db.get(Tenant, x_impersonate_tenant)
        if tenant is None or not tenant.is_active:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Tenant no encontrado.")
        _log_impersonation(db, user, tenant, x_forwarded_for)
        return tenant

    if user.tenant_id is None:
        # Interino (hasta el selector de cliente de Fase 4): un admin/miembro Zuhma sin
        # tenant asignado ve por defecto el primer cliente activo, para poder operar el
        # portal ya. Un 'client' sin tenant sí queda bloqueado.
        if user.role in (UserRole.admin, UserRole.zuhma_member):
            first = db.scalars(
                select(Tenant).where(Tenant.is_active.is_(True)).order_by(Tenant.id)
            ).first()
            if first is not None:
                return first
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Tu usuario no está asociado a ningún cliente. Contacta a Zuhma.",
        )
    tenant = db.get(Tenant, user.tenant_id)
    if tenant is None or not tenant.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tenant no encontrado o inactivo.")
    return tenant


def require_editor(user: AppUser = Depends(get_current_user)) -> AppUser:
    """Solo el equipo Zuhma (admin/zuhma_member) puede crear o editar registros.
    El cliente puede calificar y comentar, pero no crear ni modificar datos del lead."""
    if user.role not in (UserRole.admin, UserRole.zuhma_member):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Solo el equipo Zuhma puede crear o editar registros. Como cliente puedes calificar y comentar.",
        )
    return user


def get_tenant_repo(tenant: Tenant = Depends(get_current_tenant)) -> TenantOdooRepository:
    """Repositorio Odoo YA acotado al partner del tenant. Úsalo en los routers en vez
    de tocar OdooClient directo — así el aislamiento es imposible de saltar."""
    return TenantOdooRepository(get_odoo(), tenant.odoo_partner_id)


def get_lead_repo(
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
) -> "LeadRepository":
    """Repositorio del Lead Hub (Postgres) acotado al tenant activo."""
    from app.leadhub.repository import LeadRepository

    return LeadRepository(db, tenant)
