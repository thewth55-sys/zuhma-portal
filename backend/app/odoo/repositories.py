"""Repositorios Odoo ACOTADOS POR TENANT.

Cada método recibe el `company_partner_id` del tenant autenticado y fuerza el
dominio de Odoo con `('partner_id', 'child_of', company_partner_id)` — así una
factura o ticket de otro cliente NUNCA puede colarse. El aislamiento vive aquí y
en app/security/tenant.py, jamás en el frontend.

Nota de datos (verificado contra la cuenta real): las facturas y tickets a veces
cuelgan del CONTACTO hijo (p. ej. "FLORESCANO & ASOCIADOS, Claudio Barranco") y no
de la empresa. Por eso se usa `child_of` y no `=`.
"""

from __future__ import annotations

from app.odoo import mappers as m
from app.odoo.client import OdooClient


class TenantOdooRepository:
    def __init__(self, odoo: OdooClient, company_partner_id: int):
        if not company_partner_id:
            raise ValueError("company_partner_id es obligatorio: sin él no hay aislamiento.")
        self.odoo = odoo
        self.pid = company_partner_id

    def _partner_domain(self) -> list:
        return [("partner_id", "child_of", self.pid)]

    # --- Facturación (Odoo · account.move) --- #
    def list_invoices(self, limit: int = 50) -> list[dict]:
        domain = self._partner_domain() + [("move_type", "=", "out_invoice")]
        rows = self.odoo.search_read(
            "account.move", domain, m.INVOICE_FIELDS, limit=limit, order="invoice_date desc, id desc"
        )
        return [m.map_invoice(r) for r in rows]

    def get_invoice_pdf(self, invoice_id: int) -> dict | None:
        """Verifica que la factura pertenezca al tenant antes de exponer el PDF."""
        domain = self._partner_domain() + [("id", "=", invoice_id), ("move_type", "=", "out_invoice")]
        rows = self.odoo.search_read("account.move", domain, ["id", "name"], limit=1)
        return rows[0] if rows else None

    # --- Soporte (Odoo · helpdesk.ticket) --- #
    def list_tickets(self, limit: int = 50) -> list[dict]:
        rows = self.odoo.search_read(
            "helpdesk.ticket", self._partner_domain(), m.TICKET_FIELDS,
            limit=limit, order="create_date desc",
        )
        return [m.map_ticket(r) for r in rows]

    # --- Actividad reciente (Odoo · project.task) --- #
    def list_recent_tasks(self, limit: int = 8) -> list[dict]:
        rows = self.odoo.search_read(
            "project.task", self._partner_domain(), m.TASK_FIELDS,
            limit=limit, order="write_date desc",
        )
        return [m.map_task(r) for r in rows]

    # --- Archivos (Odoo · ir.attachment) --- #
    def list_documents(self, limit: int = 50) -> list[dict]:
        # ir.attachment se filtra por el partner al que pertenece el adjunto.
        rows = self.odoo.search_read(
            "ir.attachment",
            [("partner_id", "child_of", self.pid)],
            m.DOCUMENT_FIELDS,
            limit=limit,
            order="create_date desc",
        )
        return [m.map_document(r) for r in rows]
