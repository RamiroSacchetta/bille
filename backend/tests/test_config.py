"""Tests de la configuración: fuera de desarrollo no hay valores por defecto para la conexión ni los secretos."""

import pytest
from pydantic import ValidationError

from app.config import Configuracion

OBLIGATORIAS = {
    "URL_BASE_DATOS": "postgresql://bille:clave@db.ejemplo.com:5432/postgres",
    "SUPABASE_URL": "https://bille.supabase.co",
    "SUPABASE_JWT_SECRET": "un-secreto-de-produccion-de-al-menos-32-caracteres",
}


@pytest.fixture(autouse=True)
def entorno_limpio(monkeypatch):
    for nombre in [*OBLIGATORIAS, "ENTORNO"]:
        monkeypatch.delenv(nombre, raising=False)


def test_en_desarrollo_usa_los_valores_de_supabase_local():
    configuracion = Configuracion(_env_file=None)
    assert configuracion.entorno == "desarrollo"
    assert configuracion.supabase_url == "http://127.0.0.1:54321"


def test_fuera_de_desarrollo_no_arranca_sin_variables(monkeypatch):
    monkeypatch.setenv("ENTORNO", "produccion")
    with pytest.raises(ValidationError) as error:
        Configuracion(_env_file=None)
    assert "Faltan variables de entorno: URL_BASE_DATOS, SUPABASE_URL, SUPABASE_JWT_SECRET" in str(
        error.value
    )


def test_fuera_de_desarrollo_avisa_solo_las_que_faltan(monkeypatch):
    monkeypatch.setenv("ENTORNO", "produccion")
    monkeypatch.setenv("URL_BASE_DATOS", OBLIGATORIAS["URL_BASE_DATOS"])
    with pytest.raises(ValidationError) as error:
        Configuracion(_env_file=None)
    assert "Faltan variables de entorno: SUPABASE_URL, SUPABASE_JWT_SECRET" in str(error.value)


def test_fuera_de_desarrollo_rechaza_el_secreto_de_supabase_local(monkeypatch):
    monkeypatch.setenv("ENTORNO", "produccion")
    for nombre, valor in OBLIGATORIAS.items():
        monkeypatch.setenv(nombre, valor)
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "super-secret-jwt-token-with-at-least-32-characters-long")
    with pytest.raises(ValidationError) as error:
        Configuracion(_env_file=None)
    assert "SUPABASE_JWT_SECRET no puede ser el de Supabase local" in str(error.value)


def test_fuera_de_desarrollo_las_variables_vacias_cuentan_como_faltantes(monkeypatch):
    monkeypatch.setenv("ENTORNO", "produccion")
    monkeypatch.setenv("URL_BASE_DATOS", OBLIGATORIAS["URL_BASE_DATOS"])
    monkeypatch.setenv("SUPABASE_URL", "")
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "  ")
    with pytest.raises(ValidationError) as error:
        Configuracion(_env_file=None)
    assert "Faltan variables de entorno: SUPABASE_URL, SUPABASE_JWT_SECRET" in str(error.value)


def test_sin_entorno_no_acepta_el_secreto_local_con_un_supabase_de_la_nube(monkeypatch):
    monkeypatch.setenv("URL_BASE_DATOS", OBLIGATORIAS["URL_BASE_DATOS"])
    monkeypatch.setenv("SUPABASE_URL", OBLIGATORIAS["SUPABASE_URL"])
    with pytest.raises(ValidationError) as error:
        Configuracion(_env_file=None)
    assert "SUPABASE_JWT_SECRET no puede ser el de Supabase local" in str(error.value)


def test_fuera_de_desarrollo_arranca_con_todas_las_variables(monkeypatch):
    monkeypatch.setenv("ENTORNO", "produccion")
    for nombre, valor in OBLIGATORIAS.items():
        monkeypatch.setenv(nombre, valor)
    configuracion = Configuracion(_env_file=None)
    assert configuracion.supabase_url == "https://bille.supabase.co"
