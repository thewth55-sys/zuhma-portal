"""Cifrado en reposo de secretos (Fernet), con degradación segura.

Si MASTER_KEY está definida, los valores se guardan cifrados con un prefijo 'enc:v1:'.
Si no, se guardan en texto plano (con advertencia). En lectura, los valores sin prefijo
se devuelven tal cual (compatibilidad con datos previos y con la opción sin llave).
"""

from __future__ import annotations

import logging

from app.config import get_settings

logger = logging.getLogger("crypto")

_PREFIX = "enc:v1:"
_fernet = None
_loaded = False


def _fernet_obj():
    global _fernet, _loaded
    if _loaded:
        return _fernet
    _loaded = True
    key = get_settings().master_key.strip()
    if not key:
        logger.warning("MASTER_KEY no definida: los secretos se guardan SIN cifrar.")
        return None
    try:
        from cryptography.fernet import Fernet

        _fernet = Fernet(key.encode())
    except Exception as exc:  # noqa: BLE001
        logger.error("MASTER_KEY inválida (%s): secretos en texto plano.", exc)
        _fernet = None
    return _fernet


def encrypt(value: str | None) -> str | None:
    if not value:
        return value
    if value.startswith(_PREFIX):
        return value
    f = _fernet_obj()
    if f is None:
        return value
    return _PREFIX + f.encrypt(value.encode()).decode()


def decrypt(value: str | None) -> str | None:
    if value is None or not value.startswith(_PREFIX):
        return value
    f = _fernet_obj()
    if f is None:
        return value
    from cryptography.fernet import InvalidToken

    try:
        return f.decrypt(value[len(_PREFIX):].encode()).decode()
    except InvalidToken:
        logger.error("No se pudo descifrar un valor (MASTER_KEY cambiada?).")
        return value
