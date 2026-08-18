"""Punto de entrada del BFF (FastAPI).

Expone endpoints propios al frontend; NUNCA expone Odoo directo al navegador.
Fase 0: health + me/tenant + auth + aislamiento. Fase 1 añade billing/support/
files/reports/home sobre app/odoo/repositories.py.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import admin, health, ingest, leads, me, webhooks

settings = get_settings()
logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))

app = FastAPI(
    title="Zuhma Client Portal — BFF",
    version="0.1.0",
    description="Backend-for-frontend del portal de clientes de Zuhma.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(me.router)
app.include_router(leads.router)
app.include_router(admin.router)
app.include_router(ingest.router)
app.include_router(webhooks.router)


@app.get("/")
def root() -> dict:
    return {"service": "zuhma-portal-bff", "version": app.version, "docs": "/docs"}
