"""Pruebas del AISLAMIENTO multi-tenant (Definición de Hecho, sección 12).

No tocan red ni base de datos: usan un OdooClient falso que registra los `domain`
con los que se consulta. La invariante que protegemos: TODA consulta de un tenant a
Odoo lleva `('partner_id'|'*', 'child_of', <su partner_id>)`. Nunca se puede pedir a
Odoo datos sin acotar por el partner del tenant.
"""

from __future__ import annotations

import pytest

from app.odoo.repositories import TenantOdooRepository


class FakeOdoo:
    """Registra cada search_read para poder afirmar sobre el dominio usado."""

    def __init__(self):
        self.calls: list[tuple[str, list]] = []

    def search_read(self, model, domain, fields=None, limit=None, order=None):
        self.calls.append((model, domain))
        return []


PID_A = 23    # Nextcore
PID_B = 19    # Cicadehp


def _domain_pids(domain: list) -> set[int]:
    """Extrae los partner_id que aparecen en cláusulas child_of/=, del dominio."""
    pids = set()
    for clause in domain:
        if isinstance(clause, (list, tuple)) and len(clause) == 3:
            field, op, value = clause
            if "partner" in str(field) and isinstance(value, int):
                pids.add(value)
    return pids


def test_repo_requires_partner_id():
    with pytest.raises(ValueError):
        TenantOdooRepository(FakeOdoo(), 0)


@pytest.mark.parametrize("method", ["list_invoices", "list_tickets", "list_recent_tasks", "list_documents"])
def test_every_query_is_scoped_to_tenant_partner(method):
    odoo = FakeOdoo()
    repo = TenantOdooRepository(odoo, PID_A)

    getattr(repo, method)()

    assert odoo.calls, f"{method} no consultó a Odoo"
    for _model, domain in odoo.calls:
        pids = _domain_pids(domain)
        assert PID_A in pids, f"{method}: el dominio no está acotado al partner del tenant: {domain}"
        assert PID_B not in pids, f"{method}: se filtró un partner ajeno: {domain}"


def test_invoice_domain_is_child_of_not_equals():
    """Las facturas cuelgan del contacto hijo → debe usarse child_of, no '='."""
    odoo = FakeOdoo()
    TenantOdooRepository(odoo, PID_A).list_invoices()
    model, domain = odoo.calls[0]
    assert model == "account.move"
    assert any(
        c[0] == "partner_id" and c[1] == "child_of" and c[2] == PID_A
        for c in domain
        if isinstance(c, (list, tuple)) and len(c) == 3
    ), f"list_invoices debe usar child_of: {domain}"


def test_get_invoice_pdf_verifies_ownership():
    """Pedir el PDF de una factura ajena no debe devolver nada (se acota por partner)."""
    odoo = FakeOdoo()  # search_read devuelve [] → no pertenece
    result = TenantOdooRepository(odoo, PID_A).get_invoice_pdf(99999)
    assert result is None
    _model, domain = odoo.calls[0]
    assert PID_A in _domain_pids(domain)
