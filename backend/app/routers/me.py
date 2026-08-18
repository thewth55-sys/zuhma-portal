from __future__ import annotations

from fastapi import APIRouter, Depends

from app.deps import get_current_tenant, get_current_user
from app.models import AppUser, Tenant

router = APIRouter(prefix="/me", tags=["me"])


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
