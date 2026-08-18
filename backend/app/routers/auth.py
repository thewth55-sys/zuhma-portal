"""2FA por correo (código de un solo uso) exigido en cada login.

El código va al correo del usuario (Resend). La sesión queda verificada al validar el
código; persiste mientras dure esa sesión de Supabase (cada login nuevo = nuevo 2FA).
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.deps import AuthContext, get_auth_context
from app.integrations import email as mailer
from app.models import LoginOtp, MfaSession

router = APIRouter(prefix="/auth", tags=["auth"])

_TTL_MIN = 10
_MAX_ATTEMPTS = 5
_RESEND_COOLDOWN = 30  # segundos


def _hash(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


class CodeIn(BaseModel):
    code: str


@router.get("/status")
def status_endpoint(ctx: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)) -> dict:
    """¿La sesión actual ya pasó el 2FA? (sin correo o sin session_id → no se exige)."""
    if not get_settings().email_configured or not ctx.session_id:
        return {"email": ctx.user.email, "mfa_required": False, "mfa_verified": True}
    verified = bool(db.get(MfaSession, ctx.session_id))
    return {"email": ctx.user.email, "mfa_required": not verified, "mfa_verified": verified}


@router.post("/otp/send")
def send_otp(ctx: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)) -> dict:
    if not ctx.session_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La sesión no tiene identificador; vuelve a iniciar sesión.")
    if db.get(MfaSession, ctx.session_id):
        return {"sent": False, "already_verified": True}

    now = datetime.now(timezone.utc)
    existing = db.scalar(select(LoginOtp).where(LoginOtp.session_id == ctx.session_id))
    if existing:
        created = existing.created_at or now
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        if (now - created).total_seconds() < _RESEND_COOLDOWN:
            return {"sent": False, "cooldown": True}
        db.delete(existing)
        db.flush()

    code = f"{secrets.randbelow(1_000_000):06d}"
    db.add(LoginOtp(
        session_id=ctx.session_id, user_id=ctx.user.id, code_hash=_hash(code),
        expires_at=now + timedelta(minutes=_TTL_MIN),
    ))
    db.commit()

    subject, html_body = mailer.otp_email(code)
    ok, detail = mailer.send_email(ctx.user.email, subject, html_body)
    if not ok:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"No se pudo enviar el código: {detail}")
    return {"sent": True, "email": ctx.user.email}


@router.post("/otp/verify")
def verify_otp(body: CodeIn, ctx: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)) -> dict:
    if not ctx.session_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Sesión inválida.")
    if db.get(MfaSession, ctx.session_id):
        return {"verified": True}

    otp = db.scalar(select(LoginOtp).where(LoginOtp.session_id == ctx.session_id))
    if otp is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No hay un código pendiente. Solicita uno nuevo.")
    expires = otp.expires_at if otp.expires_at.tzinfo else otp.expires_at.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > expires:
        db.delete(otp)
        db.commit()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El código venció. Solicita uno nuevo.")
    if otp.attempts >= _MAX_ATTEMPTS:
        db.delete(otp)
        db.commit()
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Demasiados intentos. Solicita un código nuevo.")

    if _hash(body.code.strip()) != otp.code_hash:
        otp.attempts += 1
        db.commit()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Código incorrecto.")

    # Correcto → marca la sesión verificada y limpia el código.
    db.add(MfaSession(session_id=ctx.session_id, user_id=ctx.user.id, verified_at=datetime.now(timezone.utc)))
    db.execute(delete(LoginOtp).where(LoginOtp.session_id == ctx.session_id))
    db.commit()
    return {"verified": True}
