from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin
from app.security.types import EncryptedString


class MetaPage(Base, TimestampMixin):
    """Página de Facebook conectada a un cliente para recibir sus Meta Lead Ads.

    Guarda el Page Access Token (de larga duración) para leer los leads vía Graph API.
    NOTA: el token es sensible; a futuro conviene cifrarlo en reposo (Fernet), como el MCP.
    """

    __tablename__ = "meta_page"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), index=True)
    page_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    page_name: Mapped[str | None] = mapped_column(String(255), default=None)
    page_access_token: Mapped[str] = mapped_column(EncryptedString)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
