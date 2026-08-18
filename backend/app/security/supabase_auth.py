"""Verificación del JWT de Supabase.

El frontend hace login con el SDK de Supabase y manda el access token en
`Authorization: Bearer <jwt>`. Aquí lo validamos:
  - RS256/ES256 → contra el JWKS público del proyecto (recomendado).
  - HS256 legacy → contra SUPABASE_JWT_SECRET (solo si el proyecto aún lo usa).

Devuelve un `SupabaseIdentity` (sub, email) que app/deps.py resuelve a un AppUser.
El BFF NUNCA usa esta identidad para hablar con Odoo: eso lo hace la cuenta de
servicio; esta identidad solo sirve para saber QUÉ tenant puede ver el usuario.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import httpx
from jose import jwt
from jose.exceptions import JWTError

from app.config import get_settings

settings = get_settings()

_JWKS_CACHE: dict[str, object] = {"keys": None, "fetched_at": 0.0}
_JWKS_TTL = 3600.0


class AuthError(Exception):
    pass


@dataclass(frozen=True)
class SupabaseIdentity:
    sub: str
    email: str
    session_id: str | None = None


def _jwks() -> dict:
    now = time.time()
    if _JWKS_CACHE["keys"] and now - float(_JWKS_CACHE["fetched_at"]) < _JWKS_TTL:  # type: ignore[arg-type]
        return _JWKS_CACHE["keys"]  # type: ignore[return-value]
    url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
    resp = httpx.get(url, timeout=8.0)
    resp.raise_for_status()
    keys = resp.json()
    _JWKS_CACHE["keys"] = keys
    _JWKS_CACHE["fetched_at"] = now
    return keys


def verify_token(token: str) -> SupabaseIdentity:
    """Valida firma, expiración y audiencia. Lanza AuthError si algo falla."""
    options = {"verify_aud": bool(settings.supabase_jwt_aud)}
    try:
        header = jwt.get_unverified_header(token)
        alg = header.get("alg", "")

        if alg == "HS256":
            if not settings.supabase_jwt_secret:
                raise AuthError("Token HS256 pero SUPABASE_JWT_SECRET no está configurado.")
            claims = jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience=settings.supabase_jwt_aud or None,
                options=options,
            )
        else:
            claims = jwt.decode(
                token,
                _jwks(),
                algorithms=["RS256", "ES256"],
                audience=settings.supabase_jwt_aud or None,
                issuer=settings.supabase_jwt_issuer or None,
                options=options,
            )
    except JWTError as exc:
        raise AuthError(f"Token inválido: {exc}") from exc
    except httpx.HTTPError as exc:
        raise AuthError(f"No se pudo obtener el JWKS de Supabase: {exc}") from exc

    sub = claims.get("sub")
    email = (claims.get("email") or "").lower()
    if not sub:
        raise AuthError("El token no contiene 'sub'.")
    return SupabaseIdentity(sub=sub, email=email, session_id=claims.get("session_id"))
