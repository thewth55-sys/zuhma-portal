from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class LoginOtp(Base, TimestampMixin):
    """Código de un solo uso enviado por correo para el 2FA de una sesión."""

    __tablename__ = "login_otp"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(String(128), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("app_user.id"), index=True)
    code_hash: Mapped[str] = mapped_column(String(128))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, default=0)


class MfaSession(Base, TimestampMixin):
    """Sesión de Supabase que ya pasó el 2FA (persiste mientras dure esa sesión)."""

    __tablename__ = "mfa_session"

    session_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("app_user.id"), index=True)
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
