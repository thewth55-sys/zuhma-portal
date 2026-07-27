# Roadmap por fases

| Fase | Entregable | Alcance |
|---|---|---|
| **0** ✅ | Base | Repo, Docker, `OdooClient`, modelo cliente↔partner, auth Supabase, layout con marca, contrato Lead Hub (stub), seed de tenants. |
| **1** | MVP cliente (lectura) | Inicio, Facturación (Odoo), Soporte (Odoo), Archivos (Odoo), Reportes básicos, chat Livechat. Datos reales de Odoo. |
| **2** | Bandeja de leads + Aprobaciones | Bandeja (Lead Hub stub) con acciones Potencial/No potencial/En espera; módulo de aprobación de contenido con auto-aprobado a 2 días hábiles. |
| **3** | Atribución + pauta + consumo de plan | Conectores Meta/Google/LinkedIn (cache por lotes); vista Atribución (Lead Hub); consumo de plan real. |
| **4** | Admin + automatización | Dashboard de negocio, gestión de clientes, "ver como cliente" auditado, disparo/consumo de webhooks n8n. |

## Definición de "hecho" (todas las fases)
Código tipado y linteado · endpoints con validación y manejo de errores · **tests** de
aislamiento multi-tenant y mappers Odoo · `.env.example` documentado · instrucciones de
despliegue Easypanel · UI fiel al prototipo en desktop y móvil.
