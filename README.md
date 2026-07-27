# Zuhma Client Portal

Portal web multi-tenant para los clientes de Zuhma (agencia de marketing B2B).
Arquitectura **híbrida**: Odoo es el sistema de registro (CRM, facturación, helpdesk,
proyectos) accedido por su API externa; un **panel propio** aporta lo que Odoo no hace
(aprobación de contenido, consumo de plan, reportes de pauta y experiencia de marca); el
**Zuhma Lead Hub** (motor de atribución) se consume vía un contrato de API (hoy con stub).

- **Frontend:** Next.js (App Router) + TypeScript + TailwindCSS
- **Backend (BFF):** FastAPI (Python) — nunca expone Odoo directo al navegador
- **Base propia:** PostgreSQL (tenants, usuarios, cuotas de plan, aprobaciones, auditoría)
- **Auth:** Supabase Auth (el BFF valida el JWT)
- **Despliegue:** Docker + Easypanel (1 servicio por app)

## Estado — Fase 0 (base) ✅

| Entregable | Estado |
|---|---|
| Monorepo + estructura + Docker | ✅ |
| Capa `OdooClient` aislada (cuenta de servicio) | ✅ |
| Modelo cliente↔partner (tenant, app_user, plan_quota, content_piece, audit) | ✅ |
| Aislamiento multi-tenant + suplantación auditada | ✅ (tests en verde) |
| Auth Supabase (verificación JWT) + auto-provisión | ✅ |
| Layout con marca zühma+ (sidebar, topbar, mode switch, Livechat) | ✅ |
| Contrato Lead Hub + stub | ✅ |
| Seed de tenants piloto (Nextcore, Cicadehp, Hematia, Elsa Victoria) | ✅ |

Las 18 vistas se implementan por fases (ver `docs/roadmap.md`). Hoy cada sección
renderiza un placeholder con marca que indica su fase y origen de datos.

## Estructura

```
backend/    FastAPI BFF — app/odoo (único punto Odoo), security, models, routers, leadhub
frontend/   Next.js — app/, components/ (Shell, Sidebar…), lib/ (api, supabase, nav)
infra/      plantillas de despliegue Easypanel
docs/        modelo de datos, mapeo Odoo, seguridad
```

## Correr en local

### Opción A — Docker Compose (recomendado)
```bash
cp .env.example .env          # completa Odoo + Supabase
docker compose up --build     # db + backend (alembic + uvicorn) + frontend
# Frontend: http://localhost:3000 · BFF: http://localhost:8000/docs
```

### Opción B — sin Docker
```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env        # DATABASE_URL a tu Postgres local
alembic upgrade head
python -m scripts.seed_tenants
uvicorn app.main:app --reload  # http://localhost:8000

# Frontend (otra terminal)
cd frontend
npm install
cp .env.local.example .env.local   # llaves de Supabase (las entrega Oswaldo)
npm run dev                     # http://localhost:3000
```

> Sin llaves de Supabase, el login muestra un aviso y un botón **“Ver demo del portal”**
> para revisar el shell y la marca sin autenticación.

## Tests
```bash
cd backend && pip install -r requirements.txt
pytest        # aislamiento multi-tenant + mappers Odoo
```

## Configuración
Todas las variables están documentadas en [`.env.example`](.env.example). Lo que falta
para producción: cuenta de servicio de Odoo, proyecto Supabase, snippet de Odoo Livechat.

## Notas de seguridad / seguimiento
- **Aislamiento:** toda consulta a Odoo se acota por `partner_id child_of <tenant>` en el
  backend (`app/odoo/repositories.py`); nunca se confía en el frontend. Ver
  `tests/test_tenant_isolation.py`.
- **Dependencias:** `next` en el último parche 14.2.x (14.2.35). Migración a Next 15
  (cierra el resto de advisories de rango amplio) queda como seguimiento.
