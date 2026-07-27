from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.config import get_settings
from app.db import engine
from app.odoo import OdooError, get_odoo

router = APIRouter(tags=["health"])
settings = get_settings()


@router.get("/health")
def health() -> dict:
    """Liveness + estado de dependencias (sin filtrar secretos)."""
    db_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:  # noqa: BLE001
        db_ok = False

    odoo_ok = None
    if settings.odoo_configured:
        try:
            _ = get_odoo().uid
            odoo_ok = True
        except OdooError:
            odoo_ok = False

    return {
        "status": "ok",
        "env": settings.app_env,
        "db": db_ok,
        "odoo_configured": settings.odoo_configured,
        "odoo_auth": odoo_ok,
        "leadhub_mode": settings.leadhub_mode,
    }
