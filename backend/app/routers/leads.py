"""Bandeja de leads y detalle del lead — Lead Hub persistente (Postgres).

Todo se acota por el tenant activo (get_lead_repo → LeadRepository). El cuestionario y
el scoring son configurables por cliente (GET /leads/config). Al calificar un lead se
genera el evento de conversión (en cola hasta que el motor CAPI/Google tenga credenciales).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.deps import get_current_user, get_lead_repo, require_editor
from app.leadhub.repository import LeadRepository
from app.models import AppUser

router = APIRouter(prefix="/leads", tags=["leads"])

_VALID_STATUS = {"pending", "waiting", "potential", "discarded"}


class StatusIn(BaseModel):
    status: str


class CommentIn(BaseModel):
    text: str


class LeadIn(BaseModel):
    contact_name: str
    cargo: str | None = None
    email: str | None = None
    phone: str | None = None
    company_name: str | None = None
    company_size: str | None = None
    website: str | None = None
    channel: str | None = None
    owner: str | None = None
    description: str | None = None
    answers: dict = {}
    # atribución (normalmente la rellena el snippet/webhook; editable en alta manual)
    gclid: str | None = None
    fbclid: str | None = None
    fbc: str | None = None
    fbp: str | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None


class LeadPatch(BaseModel):
    contact_name: str | None = None
    cargo: str | None = None
    email: str | None = None
    phone: str | None = None
    company_name: str | None = None
    company_size: str | None = None
    website: str | None = None
    channel: str | None = None
    owner: str | None = None
    description: str | None = None
    answers: dict | None = None


@router.get("/config")
def config(repo: LeadRepository = Depends(get_lead_repo)) -> dict:
    """Cuestionario + reglas de scoring del cliente (para renderizar el formulario)."""
    return repo.get_config()


@router.get("/kpis")
def kpis(repo: LeadRepository = Depends(get_lead_repo)) -> dict:
    return repo.kpis()


@router.get("")
def list_leads(status_filter: str | None = None, repo: LeadRepository = Depends(get_lead_repo)) -> dict:
    return repo.list_leads(status_filter)


@router.get("/{lead_id}")
def get_lead(lead_id: str, repo: LeadRepository = Depends(get_lead_repo)) -> dict:
    detail = repo.get(lead_id)
    if detail is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead no encontrado.")
    return detail


# --- Crear / editar: SOLO equipo Zuhma (require_editor) --- #

@router.post("", status_code=status.HTTP_201_CREATED)
def create_lead(
    body: LeadIn,
    repo: LeadRepository = Depends(get_lead_repo),
    _: AppUser = Depends(require_editor),
) -> dict:
    if not body.contact_name.strip():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "El nombre del contacto es obligatorio.")
    return repo.create(body.model_dump())


@router.patch("/{lead_id}")
def update_lead(
    lead_id: str,
    body: LeadPatch,
    repo: LeadRepository = Depends(get_lead_repo),
    _: AppUser = Depends(require_editor),
) -> dict:
    updated = repo.update(lead_id, body.model_dump(exclude_none=True))
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead no encontrado.")
    return updated


# --- Calificar y comentar: cliente + equipo Zuhma --- #

@router.post("/{lead_id}/status")
def set_status(lead_id: str, body: StatusIn, repo: LeadRepository = Depends(get_lead_repo)) -> dict:
    if body.status not in _VALID_STATUS:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Estado inválido: {body.status}")
    try:
        updated = repo.set_status(lead_id, body.status)
    except KeyError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Estado inválido: {body.status}")
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead no encontrado.")
    # Al calificar (potential) se generó el evento de conversión; intentamos enviarlo.
    from app.leadhub import conversions
    conversions.flush_lead(repo.db, repo.tenant, lead_id)
    return repo.get(lead_id) or updated


@router.post("/{lead_id}/comment")
def add_comment(
    lead_id: str,
    body: CommentIn,
    repo: LeadRepository = Depends(get_lead_repo),
    user: AppUser = Depends(get_current_user),
) -> dict:
    if not body.text.strip():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "El comentario no puede estar vacío.")
    author = user.full_name or user.email
    updated = repo.add_comment(lead_id, body.text.strip(), author)
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead no encontrado.")
    return updated
