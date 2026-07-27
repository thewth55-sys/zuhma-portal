"""Motor y sesión de SQLAlchemy para la base de datos PROPIA del portal.

Esta base guarda solo lo que Odoo no debe: tenants, usuarios de la app, cuotas de
plan, piezas de contenido y auditoría de suplantación. Odoo sigue siendo la fuente
de verdad para CRM/facturación/helpdesk/proyectos (se accede vía app/odoo/).
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Iterator[Session]:
    """Dependencia FastAPI: una sesión por request, siempre cerrada al final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
