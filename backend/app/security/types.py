"""Tipo de columna que cifra/descifra transparentemente (Fernet)."""

from __future__ import annotations

from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator

from app.security import crypto


class EncryptedString(TypeDecorator):
    """String que se guarda cifrado en la BD y se descifra al leer.

    Sin MASTER_KEY, se comporta como Text plano (degradación segura).
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return crypto.encrypt(value)

    def process_result_value(self, value, dialect):
        return crypto.decrypt(value)
