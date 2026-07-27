# Mapeo Odoo → Portal (verificado contra la cuenta real, 2026-07-27)

Origen de datos por sección (arquitectura híbrida, sección 6 de la evaluación):

| Sección | Origen | Modelo Odoo / Fuente | Notas |
|---|---|---|---|
| Facturación | Odoo | `account.move` (`move_type=out_invoice`) | Filtrar `partner_id child_of <tenant>` (las facturas cuelgan del contacto hijo). |
| Soporte | Odoo | `helpdesk.ticket` | `partner_id` presente; hay equipos por cliente (p. ej. "Nextcore" id 3). |
| Actividad / Planeación | Odoo | `project.task` | ⚠️ Los proyectos casi no tienen `partner_id` (usan convención de nombre). Fase 3 necesita tabla de mapeo proyecto↔tenant. |
| Archivos | Odoo | `ir.attachment` | Filtrar por `partner_id child_of`. |
| Bandeja de leads | Lead Hub | contrato `app/leadhub` (stub) | `crm.lead` es el pipeline de ventas de Zuhma, NO los leads del cliente. |
| Atribución | Lead Hub | contrato `app/leadhub` (stub) | Lead ID, CAPI match rate, GCLID. |
| Embudo comercial (Reportes) | — | **solo muestra** | Decisión de producto: datos de ejemplo, no cableado. |
| Reportes de pauta | Panel + Ads | Meta/Google/LinkedIn (Fase 3) | Cachear por lotes. |
| Consumo de plan, Aprobaciones | Panel | BD propia | Odoo no lo modela. |

## Tenants piloto ↔ partner IDs (reales)

| slug | Cliente | `odoo_partner_id` | Plan |
|---|---|---|---|
| nextcore | Nextcore Consulting, S.C. | 23 | Growth B2B |
| cicadehp | Grupo Cicadehp | 19 | Growth B2B |
| hematia | Hematia Retorno a la Salud | 184 | Growth |
| elsa-victoria | Elsa Victoria Hernández Ruiz | 355 | Lite |

> Los clientes del prototipo (Franquicia tu Éxito 539, COMDAF 544, "Marca Urbana" —
> inexistente) eran de relleno. Se sembraron los clientes con datos reales.

## Etapas reales (para mappers)
- **CRM** (`crm.stage`): Retenidas · Calificado · Acercamiento · Propuesta · Seguimiento · Firma de Contrato · Won.
- **Helpdesk** (`helpdesk.stage`): New · In Progress · En Espera · Pausado · Solved · Cerrado · Finalizado (ids duplicados por equipo).

## Migración XML-RPC → JSON-2 (invierno 2027)
Todo el acceso a Odoo vive en `app/odoo/client.py`. Migrar = reimplementar esa clase;
mappers, repositorios y routers no cambian.
