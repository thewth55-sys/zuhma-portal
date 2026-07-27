"""Configuración central del BFF (pydantic-settings).

Un solo lugar donde se leen las variables de entorno. No se importa nada de Odoo
ni de la base de datos aquí para mantenerlo libre de efectos secundarios.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- App ---
    app_env: str = "development"
    log_level: str = "INFO"
    cors_allow_origins: str = "http://localhost:3000"
    # Emails con rol elevado (admin / miembro Zuhma) al iniciar sesión.
    zuhma_admin_emails: str = ""

    # --- Base de datos propia ---
    database_url: str = "postgresql+psycopg://zuhma:zuhma@localhost:5432/zuhma_portal"

    # --- Odoo (cuenta de servicio) ---
    odoo_url: str = ""
    odoo_db: str = ""
    odoo_service_login: str = ""
    odoo_service_api_key: str = ""

    # --- Supabase Auth ---
    supabase_url: str = ""
    supabase_jwt_issuer: str = ""
    supabase_jwt_aud: str = "authenticated"
    supabase_jwt_secret: str = ""  # solo si usas HS256 legacy

    # --- Lead Hub ---
    leadhub_mode: str = "stub"  # stub | live
    leadhub_base_url: str = ""

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]

    @property
    def admin_emails(self) -> set[str]:
        return {e.strip().lower() for e in self.zuhma_admin_emails.split(",") if e.strip()}

    @property
    def odoo_configured(self) -> bool:
        return bool(self.odoo_url and self.odoo_db and self.odoo_service_login and self.odoo_service_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
