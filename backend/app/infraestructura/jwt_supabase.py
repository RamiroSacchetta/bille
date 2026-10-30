"""Validación de los tokens que emite Supabase Auth.

Supabase firma con HS256 (secreto compartido) o con claves asimétricas publicadas en su JWKS,
según la configuración del proyecto. Se aceptan ambas.
"""

from functools import lru_cache
from uuid import UUID

import jwt

from app.config import configuracion

ALGORITMOS_PERMITIDOS = {"HS256", "ES256", "RS256"}
# El reloj de Supabase y el de la API no están sincronizados al milisegundo: sin tolerancia,
# un token recién emitido puede rechazarse por traer un `iat` apenas en el futuro.
TOLERANCIA_RELOJ_SEGUNDOS = 30


class TokenInvalido(Exception):
    pass


@lru_cache
def _cliente_jwks() -> jwt.PyJWKClient:
    return jwt.PyJWKClient(f"{configuracion().supabase_url}/auth/v1/.well-known/jwks.json")


def usuario_del_token(token: str) -> UUID:
    try:
        algoritmo = jwt.get_unverified_header(token).get("alg")
        if algoritmo not in ALGORITMOS_PERMITIDOS:
            raise TokenInvalido("Algoritmo de firma no permitido")
        if algoritmo == "HS256":
            clave = configuracion().supabase_jwt_secret
        else:
            clave = _cliente_jwks().get_signing_key_from_jwt(token).key
        # Un solo algoritmo por token: evita la confusión de algoritmos entre secreto y clave pública
        datos = jwt.decode(
            token,
            clave,
            algorithms=[algoritmo],
            audience="authenticated",
            options={"require": ["exp", "sub"]},
            leeway=TOLERANCIA_RELOJ_SEGUNDOS,
        )
        return UUID(datos["sub"])
    except (jwt.PyJWTError, ValueError, KeyError) as error:
        raise TokenInvalido("La sesión no es válida o venció") from error
