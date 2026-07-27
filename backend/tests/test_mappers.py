"""Pruebas de los mappers Odoo → DTO (funciones puras, sin red)."""

from __future__ import annotations

from app.odoo import mappers as m


def test_map_invoice_shapes_relational_fields():
    raw = {
        "id": 608,
        "name": "INV/2026/00066",
        "partner_id": [355, "ELSA VICTORIA HERNANDEZ RUIZ"],
        "invoice_date": "2026-07-23",
        "invoice_date_due": False,
        "amount_total": 2900.54,
        "amount_residual": 0.0,
        "currency_id": [33, "MXN"],
        "state": "posted",
        "payment_state": "paid",
    }
    dto = m.map_invoice(raw)
    assert dto["number"] == "INV/2026/00066"
    assert dto["partner"] == "ELSA VICTORIA HERNANDEZ RUIZ"
    assert dto["currency"] == "MXN"
    assert dto["state"] == "Publicada"
    assert dto["payment_state"] == "pagada"
    assert dto["due_date"] is None  # False de Odoo → None


def test_map_invoice_draft_without_number():
    raw = {"id": 163, "name": False, "partner_id": [355, "X"], "amount_total": 261,
           "state": "draft", "payment_state": "not_paid"}
    dto = m.map_invoice(raw)
    assert dto["number"] == "(borrador)"
    assert dto["state"] == "Borrador"
    assert dto["payment_state"] == "pendiente"


def test_map_ticket():
    raw = {
        "id": 264, "name": "Revisión de campañas",
        "team_id": [3, "Nextcore"], "stage_id": [2, "In Progress"],
        "user_id": False, "priority": "2", "kanban_state": "normal",
        "create_date": "2026-07-20 17:55:31", "write_date": "2026-07-21 09:00:00",
    }
    dto = m.map_ticket(raw)
    assert dto["team"] == "Nextcore"
    assert dto["stage"] == "In Progress"
    assert dto["assignee"] is None  # user_id False → None
