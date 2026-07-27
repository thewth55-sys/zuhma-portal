"""Capa ÚNICA de acceso a Odoo — reutilizada del MCP `odoo-projects-mcp` (server.py).

Diferencia clave con el MCP: allí cada usuario actúa con su propia identidad (token
por persona). Aquí el BFF usa UNA cuenta de SERVICIO, y el aislamiento por cliente NO
lo da Odoo sino el backend (ver app/security/tenant.py): cada consulta se acota por el
`partner_id` del tenant autenticado. Nunca se confía en el frontend para filtrar.

Odoo retirará XML-RPC en favor de la External JSON-2 API (Online 21.1, invierno 2027).
Toda la E/S con Odoo vive AQUÍ para que esa migración no toque el resto del portal.
"""

from __future__ import annotations

import xmlrpc.client
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from app.config import get_settings


class OdooError(RuntimeError):
    """Error legible al hablar con Odoo."""


@dataclass(frozen=True)
class OdooCredentials:
    login: str
    api_key: str


class OdooClient:
    """Cliente XML-RPC fino. Cachea el uid autenticado por (db, login) durante la
    vida del proceso para no re-autenticar en cada llamada.

    Portado de OdooClient en odoo-projects-mcp/server.py (misma superficie de API:
    execute / search_read / create / write / unlink) para migración sin fricción.
    """

    _uid_cache: dict[str, int] = {}

    def __init__(self, url: str, db: str, creds: OdooCredentials):
        self.url = url.rstrip("/")
        self.db = db
        self.creds = creds
        self._common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common", allow_none=True)
        self._models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object", allow_none=True)

    @property
    def uid(self) -> int:
        cache_key = f"{self.db}:{self.creds.login}"
        cached = self._uid_cache.get(cache_key)
        if cached:
            return cached
        try:
            uid = self._common.authenticate(self.db, self.creds.login, self.creds.api_key, {})
        except Exception as exc:  # noqa: BLE001
            raise OdooError(f"No se pudo contactar con Odoo: {exc}") from exc
        if not uid:
            raise OdooError(
                "Autenticación de Odoo fallida. Revisa ODOO_SERVICE_LOGIN / "
                "ODOO_SERVICE_API_KEY y que la cuenta de servicio tenga acceso a los módulos."
            )
        self._uid_cache[cache_key] = uid
        return uid

    def execute(self, model: str, method: str, args: list | None = None, kwargs: dict | None = None) -> Any:
        try:
            return self._models.execute_kw(
                self.db, self.uid, self.creds.api_key, model, method, args or [], kwargs or {}
            )
        except xmlrpc.client.Fault as fault:
            raise OdooError(f"Odoo rechazó la operación ({model}.{method}): {fault.faultString}") from fault
        except OdooError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise OdooError(f"Error llamando a Odoo ({model}.{method}): {exc}") from exc

    # ---- Azúcar sobre el ORM ------------------------------------------------ #

    def search_read(
        self,
        model: str,
        domain: list,
        fields: list[str] | None = None,
        limit: int | None = None,
        order: str | None = None,
    ) -> list[dict]:
        kwargs: dict[str, Any] = {"fields": fields or []}
        if limit:
            kwargs["limit"] = limit
        if order:
            kwargs["order"] = order
        return self.execute(model, "search_read", [domain], kwargs)

    def read(self, model: str, ids: list[int], fields: list[str] | None = None) -> list[dict]:
        return self.execute(model, "read", [ids], {"fields": fields or []})

    def search_count(self, model: str, domain: list) -> int:
        return self.execute(model, "search_count", [domain])

    def create(self, model: str, values: dict) -> int:
        return self.execute(model, "create", [values])

    def write(self, model: str, ids: list[int], values: dict) -> bool:
        return self.execute(model, "write", [ids, values])

    def unlink(self, model: str, ids: list[int]) -> bool:
        return self.execute(model, "unlink", [ids])


@lru_cache
def get_odoo() -> OdooClient:
    """OdooClient de la cuenta de servicio (singleton por proceso)."""
    s = get_settings()
    if not s.odoo_configured:
        raise OdooError(
            "Odoo no está configurado. Define ODOO_URL, ODOO_DB, ODOO_SERVICE_LOGIN "
            "y ODOO_SERVICE_API_KEY en el entorno."
        )
    return OdooClient(s.odoo_url, s.odoo_db, OdooCredentials(s.odoo_service_login, s.odoo_service_api_key))
