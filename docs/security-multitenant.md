# Seguridad multi-tenant

## Cadena de aislamiento
```
Authorization: Bearer <jwt Supabase>
  → verify_token()        firma / exp / audiencia (JWKS del proyecto)
  → get_current_user()    AppUser en BD propia (auto-provisión en 1er login; rol por lista de admins)
  → get_current_tenant()  el tenant que el usuario PUEDE ver
  → get_tenant_repo()     TenantOdooRepository acotado por partner_id del tenant
```

## Reglas
1. **El backend decide, nunca el frontend.** Toda consulta a Odoo pasa por
   `TenantOdooRepository`, que fuerza `('partner_id', 'child_of', tenant.odoo_partner_id)`.
   Sin `company_partner_id` el repositorio lanza error (no hay consulta "sin acotar").
2. **Roles:** `client` (solo su tenant), `zuhma_member` y `admin` (pueden suplantar).
3. **"Ver como cliente":** solo roles elevados, vía cabecera `X-Impersonate-Tenant`.
   Cada suplantación se registra en `impersonation_audit` (admin, tenant, inicio, IP) y
   el frontend la marca visualmente (banner en Topbar).
4. **La identidad del cliente NUNCA habla con Odoo.** El BFF usa una cuenta de servicio;
   el JWT de Supabase solo determina QUÉ tenant puede ver el usuario.

## Pruebas (Definición de Hecho)
`backend/tests/test_tenant_isolation.py` verifica, sin red, que:
- ningún método del repositorio consulta Odoo sin el `partner_id` del tenant;
- no se filtra el partner de otro cliente;
- las facturas usan `child_of` (no `=`);
- pedir el PDF de una factura ajena devuelve vacío.

## Pendiente (fases siguientes)
- PII/financiero: cifrado en reposo de campos sensibles, retención y DPA.
- Rate limiting en el BFF; logs sin tokens.
- Postgres Row Level Security como segunda barrera (defensa en profundidad).
