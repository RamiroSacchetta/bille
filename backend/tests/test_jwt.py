"""Tests de la validación de tokens: secreto compartido (Supabase local) y claves asimétricas (JWKS, la nube)."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec

from app.config import configuracion
from app.infraestructura import jwt_supabase
from app.infraestructura.jwt_supabase import TokenInvalido, usuario_del_token


def _datos(usuario):
    return {"sub": str(usuario), "aud": "authenticated", "exp": datetime.now(UTC) + timedelta(hours=1)}


@pytest.fixture
def clave_de_la_nube(monkeypatch):
    """Simula el JWKS de un proyecto de Supabase que firma con ES256."""
    clave = ec.generate_private_key(ec.SECP256R1())
    publica = SimpleNamespace(key=clave.public_key())
    monkeypatch.setattr(
        jwt_supabase, "_cliente_jwks", lambda: SimpleNamespace(get_signing_key_from_jwt=lambda _: publica)
    )
    return clave


def test_acepta_un_token_firmado_con_la_clave_del_jwks(clave_de_la_nube):
    usuario = uuid4()
    token = jwt.encode(_datos(usuario), clave_de_la_nube, algorithm="ES256", headers={"kid": "clave-1"})

    assert usuario_del_token(token) == usuario


def test_rechaza_un_token_firmado_con_otra_clave(clave_de_la_nube):
    otra = ec.generate_private_key(ec.SECP256R1())
    token = jwt.encode(_datos(uuid4()), otra, algorithm="ES256", headers={"kid": "clave-1"})

    with pytest.raises(TokenInvalido):
        usuario_del_token(token)


def test_acepta_un_token_con_el_secreto_compartido():
    usuario = uuid4()
    token = jwt.encode(_datos(usuario), configuracion().supabase_jwt_secret, algorithm="HS256")

    assert usuario_del_token(token) == usuario


def test_rechaza_un_token_sin_firma():
    token = jwt.encode(_datos(uuid4()), None, algorithm="none")

    with pytest.raises(TokenInvalido):
        usuario_del_token(token)
