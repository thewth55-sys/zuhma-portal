from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin
from app.security.types import EncryptedString


class ConversionConfig(Base, TimestampMixin):
    """Credenciales de conversión por cliente (Meta CAPI / Google Ads). Secretos cifrados."""

    __tablename__ = "conversion_config"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), unique=True, index=True)

    # --- Meta Conversions API ---
    meta_pixel_id: Mapped[str | None] = mapped_column(String(64), default=None)         # dataset/pixel id
    meta_capi_token: Mapped[str | None] = mapped_column(EncryptedString, default=None)  # access token CAPI
    meta_test_event_code: Mapped[str | None] = mapped_column(String(64), default=None)  # opcional, para pruebas

    # --- Google Ads Offline Conversions ---
    google_customer_id: Mapped[str | None] = mapped_column(String(32), default=None)
    google_login_customer_id: Mapped[str | None] = mapped_column(String(32), default=None)
    google_conversion_action_id: Mapped[str | None] = mapped_column(String(64), default=None)
    google_developer_token: Mapped[str | None] = mapped_column(EncryptedString, default=None)
    google_client_id: Mapped[str | None] = mapped_column(String(255), default=None)
    google_client_secret: Mapped[str | None] = mapped_column(EncryptedString, default=None)
    google_refresh_token: Mapped[str | None] = mapped_column(EncryptedString, default=None)

    @property
    def meta_ready(self) -> bool:
        return bool(self.meta_pixel_id and self.meta_capi_token)

    @property
    def google_ready(self) -> bool:
        return bool(
            self.google_customer_id and self.google_conversion_action_id
            and self.google_developer_token and self.google_client_id
            and self.google_client_secret and self.google_refresh_token
        )
