# Despliegue en Easypanel — primer deploy

Repo: **`thewth55-sys/zuhma-portal`** (privado). Un proyecto de Easypanel con **3 servicios**
desde el mismo monorepo: `db` (Postgres), `backend` (FastAPI) y `frontend` (Next.js).

```
GitHub (privado) ──push a main──► Easypanel: build por servicio (Dockerfile) ──► HTTPS auto
   db (Postgres)              backend → api-portal.zuhma.online
                             frontend → portal.zuhma.online
```

Dominios sugeridos (ajústalos a los tuyos): frontend `portal.zuhma.online`, backend
`api-portal.zuhma.online`.

---

## 0) Conectar GitHub a Easypanel (una vez)
En Easypanel → *Settings → Git/GitHub* → instala la GitHub App y **autoriza el repo
privado** `zuhma-portal`. Así Easypanel puede clonar y auto-desplegar en cada push.

Crea un **Project** nuevo, p. ej. `zuhma-portal`.

## 1) Servicio `db` (Postgres)
1. *+ Service → Postgres*. Nombre: `db`.
2. Elige versión 16. Guarda **usuario, contraseña, host interno y nombre de BD**.
   El host interno suele ser el nombre del servicio (`db`) dentro del proyecto.
3. Deploy. No expongas el puerto a internet (solo acceso interno).

## 2) Servicio `backend` (FastAPI)
1. *+ Service → App*. Nombre: `backend`. Fuente: **GitHub** → repo `zuhma-portal`, branch `main`.
2. **Build:**
   - Build method: **Dockerfile**
   - Build context / path: `backend`
   - Dockerfile path: `backend/Dockerfile`
3. **Environment:** pega las variables de [`env-vars.md`](env-vars.md) → sección `backend`.
   - `DATABASE_URL` = `postgresql+psycopg://USER:PASS@db:5432/DB` (usa los datos del paso 1;
     el host es el nombre del servicio Postgres dentro del proyecto).
   - `CORS_ALLOW_ORIGINS` = `https://portal.zuhma.online`
4. **Domains:** añade `api-portal.zuhma.online`, puerto interno **8000**, HTTPS on.
5. Deploy. En el arranque el contenedor corre `alembic upgrade head` (crea las tablas) y luego uvicorn.
6. **Comprobación:** abre `https://api-portal.zuhma.online/health` → debe responder
   `{"status":"ok","db":true,"odoo_auth":true,...}`. Si `odoo_auth:false`, revisa las 4 vars de Odoo.

## 3) Sembrar los tenants (una sola vez)
En el servicio `backend` → *Console/Terminal* de Easypanel:
```bash
python -m scripts.seed_tenants
```
Crea los tenants piloto (Nextcore, Cicadehp, Hematia, Elsa Victoria) ↔ sus partner de Odoo.

## 4) Servicio `frontend` (Next.js)
1. *+ Service → App*. Nombre: `frontend`. Fuente: **GitHub** → `zuhma-portal`, branch `main`.
2. **Build:**
   - Build method: **Dockerfile**
   - Build context / path: `frontend`
   - Dockerfile path: `frontend/Dockerfile`
3. **Environment:** variables `NEXT_PUBLIC_*` de [`env-vars.md`](env-vars.md).
   ⚠️ Deben estar **antes** del build (Next las hornea en `next build`).
   - `NEXT_PUBLIC_API_BASE_URL` = `https://api-portal.zuhma.online`
4. **Domains:** añade `portal.zuhma.online`, puerto interno **3000**, HTTPS on.
5. Deploy.

## 5) Verificación end-to-end
1. `https://api-portal.zuhma.online/health` → `db:true`, `odoo_auth:true`.
2. `https://portal.zuhma.online` → carga el login zühma+.
3. Crea un usuario en **Supabase → Authentication → Users** con el email del cliente y
   asócialo a su tenant (en Fase 1 se automatiza; por ahora, set del `tenant_id` en `app_user`).
4. Inicia sesión → deberías ver el portal del tenant con sus datos reales de Odoo.

## Despliegues siguientes
`git push` a `main` → Easypanel reconstruye y redespliega automáticamente. Las **migraciones**
corren solas en cada arranque del backend (`alembic upgrade head`).

## Checklist de seguridad
- [ ] Repo **privado** (ok).
- [ ] Ningún `.env` en Git — los secretos viven solo en Easypanel.
- [ ] Postgres sin puerto público.
- [ ] HTTPS forzado en ambos dominios.
- [ ] `ZUHMA_ADMIN_EMAILS` acotado a tu equipo (define quién es admin y puede suplantar).
