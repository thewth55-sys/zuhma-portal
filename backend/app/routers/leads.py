"""Bandeja de leads — sobre el Zuhma Lead Hub (hoy stub).

Todo se acota por el tenant activo (get_current_tenant). El Lead Hub es multi-tenant
nativo: cada método recibe el partner del tenant. Con el stub los datos son de muestra
(iguales para todo tenant); al conectar el Lead Hub real, esta capa no cambia.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.deps import get_current_tenant
from app.leadhub import get_leadhub
from app.models import Tenant

router = APIRouter(prefix="/leads", tags=["leads"])

# Estados válidos y a qué acción del prototipo corresponden.
_VALID_STATUS = {"pending", "waiting", "potential", "discarded"}


class StatusIn(BaseModel):
    status: str


class NewLeadIn(BaseModel):
    name: str
    channel: str | None = None
    contact: str | None = None


@router.get("/kpis")
def kpis(tenant: Tenant = Depends(get_current_tenant)) -> dict:
    return get_leadhub().lead_kpis(tenant.odoo_partner_id)


@router.get("")
def list_leads(status_filter: str | None = None, tenant: Tenant = Depends(get_current_tenant)) -> dict:
    """Lista de leads. `status_filter` opcional: pending|waiting|potential|discarded|all."""
    leads = get_leadhub().list_leads(tenant.odoo_partner_id, status_filter)
    # Conteo por estado para las pestañas (siempre sobre el total, sin filtrar).
    allof = get_leadhub().list_leads(tenant.odoo_partner_id, "all")
    counts = {s: sum(1 for lead in allof if lead["status"] == s) for s in _VALID_STATUS}
    counts["all"] = len(allof)
    return {"leads": leads, "counts": counts}


@router.post("/{lead_id}/status")
def set_status(lead_id: str, body: StatusIn, tenant: Tenant = Depends(get_current_tenant)) -> dict:
    if body.status not in _VALID_STATUS:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Estado inválido: {body.status}")
    try:
        return get_leadhub().set_lead_status(tenant.odoo_partner_id, lead_id, body.status)
    except KeyError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead no encontrado.")


@router.post("", status_code=status.HTTP_201_CREATED)
def add_lead(body: NewLeadIn, tenant: Tenant = Depends(get_current_tenant)) -> dict:
    if not body.name.strip():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "El nombre es obligatorio.")
    return get_leadhub().add_lead(
        tenant.odoo_partner_id, body.name.strip(), body.channel or "", body.contact or ""
    )
