"""Modelos de la base PROPIA del portal (no Odoo)."""

from app.models.base import Base
from app.models.tenant import Tenant
from app.models.user import ALL_PERMISSIONS, AppUser, UserRole
from app.models.plan import Plan, PlanQuota
from app.models.content import ContentPiece, ContentStatus
from app.models.audit import ImpersonationAudit
from app.models.lead import (
    EventStatus,
    Lead,
    LeadActivity,
    LeadConfig,
    LeadEvent,
    LeadStatus,
)
from app.models.meta import MetaPage
from app.models.conversion import ConversionConfig
from app.models.auth import LoginOtp, MfaSession

__all__ = [
    "Base",
    "Tenant",
    "AppUser",
    "UserRole",
    "Plan",
    "PlanQuota",
    "ContentPiece",
    "ContentStatus",
    "ImpersonationAudit",
    "Lead",
    "LeadEvent",
    "LeadActivity",
    "LeadConfig",
    "LeadStatus",
    "EventStatus",
    "MetaPage",
    "ConversionConfig",
    "LoginOtp",
    "MfaSession",
]
