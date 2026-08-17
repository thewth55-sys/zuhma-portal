# Variables de entorno por servicio (Easypanel)

> Los **valores** se ponen en Easypanel → cada servicio → *Environment*. **Nunca** en Git.
> Aquí solo están los **nombres** y de dónde sale cada valor.

## Servicio `backend` (FastAPI)

| Variable | Valor / origen |
|---|---|
| `DATABASE_URL` | Cadena del Postgres de Easypanel, con driver: `postgresql+psycopg://USER:PASS@HOST:5432/DB` |
| `ODOO_URL` | URL de tu Odoo Online (sin `/` final) |
| `ODOO_DB` | Nombre de la base de Odoo |
| `ODOO_SERVICE_LOGIN` | Login del usuario de servicio de Odoo |
| `ODOO_SERVICE_API_KEY` | API key de ese usuario (**secreto**) |
| `SUPABASE_URL` | `https://XXXX.supabase.co` |
| `SUPABASE_JWT_ISSUER` | `https://XXXX.supabase.co/auth/v1` |
| `SUPABASE_JWT_AUD` | `authenticated` |
| `SUPABASE_SERVICE_ROLE_KEY` | service_role de Supabase (**secreto**, solo backend) — para invitar usuarios desde el panel admin |
| `CORS_ALLOW_ORIGINS` | Dominio del frontend, p. ej. `https://portal.zuhma.online` |
| `ZUHMA_ADMIN_EMAILS` | Emails con rol admin, coma-separados (p. ej. `oswaldo@zuhma.online`) |
| `LEADHUB_MODE` | `stub` (cambia a `live` cuando exista el Lead Hub) |
| `APP_ENV` | `production` |
| `LOG_LEVEL` | `INFO` |

> No hace falta `SUPABASE_JWT_SECRET` (usamos JWKS). El `service_role` **sí** se usa ahora
> (solo backend) para invitar usuarios desde el panel admin.

## Servicio `frontend` (Next.js)

> ⚠️ Los `NEXT_PUBLIC_*` se hornean en `next build`. Deben existir **antes** de construir.

| Variable | Valor / origen |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | `https://XXXX.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | anon key de Supabase (público por diseño) |
| `NEXT_PUBLIC_API_BASE_URL` | URL pública del backend, p. ej. `https://api-portal.zuhma.online` |
| `NEXT_PUBLIC_ODOO_LIVECHAT_URL` | Host de tu Odoo (para el snippet de Livechat) |
| `NEXT_PUBLIC_ODOO_LIVECHAT_CHANNEL` | Id del canal de Livechat |

## Servicio `db` (Postgres)
Créalo como plantilla **Postgres** de Easypanel. Anota usuario/clave/host/DB para armar el
`DATABASE_URL` del backend. No necesita variables extra.
