"""Mappers Odoo → DTOs del portal.

Funciones puras (dict de Odoo → dict del portal). Se testean sin red (ver
tests/test_mappers.py). Aíslan al frontend de la forma cruda de Odoo (p. ej. los
campos relacionales que Odoo devuelve como `[id, "Nombre"]`).
"""

from __future__ import annotations

from typing import Any


def _rel_name(value: Any) -> str | None:
    """Odoo devuelve los many2one como [id, 'Nombre'] o False."""
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return value[1]
    return None


def _rel_id(value: Any) -> int | None:
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return value[0]
    return None


# --- account.move (facturas de cliente) ------------------------------------ #

_INVOICE_STATE = {"draft": "Borrador", "posted": "Publicada", "cancel": "Cancelada"}
_PAYMENT_STATE = {
    "not_paid": "pendiente",
    "in_payment": "en_pago",
    "paid": "pagada",
    "partial": "parcial",
    "reversed": "revertida",
}


def map_invoice(raw: dict) -> dict:
    return {
        "id": raw["id"],
        "number": raw.get("name") or "(borrador)",
        "partner": _rel_name(raw.get("partner_id")),
        "date": raw.get("invoice_date") or None,
        "due_date": raw.get("invoice_date_due") or None,
        "amount_total": raw.get("amount_total", 0.0),
        "amount_residual": raw.get("amount_residual", 0.0),
        "currency": _rel_name(raw.get("currency_id")) or "MXN",
        "state": _INVOICE_STATE.get(raw.get("state"), raw.get("state")),
        "payment_state": _PAYMENT_STATE.get(raw.get("payment_state"), raw.get("payment_state")),
    }


INVOICE_FIELDS = [
    "id", "name", "partner_id", "invoice_date", "invoice_date_due",
    "amount_total", "amount_residual", "currency_id", "state", "payment_state",
]


# --- helpdesk.ticket -------------------------------------------------------- #

def map_ticket(raw: dict) -> dict:
    return {
        "id": raw["id"],
        "name": raw.get("name"),
        "team": _rel_name(raw.get("team_id")),
        "stage": _rel_name(raw.get("stage_id")),
        "assignee": _rel_name(raw.get("user_id")),
        "priority": raw.get("priority"),
        "kanban_state": raw.get("kanban_state"),
        "created": raw.get("create_date"),
        "updated": raw.get("write_date"),
    }


TICKET_FIELDS = [
    "id", "name", "team_id", "stage_id", "user_id",
    "priority", "kanban_state", "create_date", "write_date",
]


# --- project.task (actividad / planeación) ---------------------------------- #

def map_task(raw: dict) -> dict:
    return {
        "id": raw["id"],
        "name": raw.get("name"),
        "project": _rel_name(raw.get("project_id")),
        "stage": _rel_name(raw.get("stage_id")),
        "assignee": _rel_name(raw.get("user_id")),
        "deadline": raw.get("date_deadline") or None,
        "updated": raw.get("write_date"),
    }


TASK_FIELDS = ["id", "name", "project_id", "stage_id", "user_id", "date_deadline", "write_date"]


# --- ir.attachment / documents (archivos) ----------------------------------- #

def map_document(raw: dict) -> dict:
    return {
        "id": raw["id"],
        "name": raw.get("name"),
        "mimetype": raw.get("mimetype"),
        "size": raw.get("file_size"),
        "created": raw.get("create_date"),
    }


DOCUMENT_FIELDS = ["id", "name", "mimetype", "file_size", "create_date"]
