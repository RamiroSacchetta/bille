"""Tests de integración contra el Supabase local (`npm run bd:iniciar`).

Crean dos cuentas reales con Supabase Auth y prueban la API con sus tokens:
el modelo de plata de punta a punta y que una cuenta no vea los datos de la otra (S1).
Se saltean si el Supabase local no está corriendo.
"""

from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import configuracion
from app.main import crear_app

pytestmark = pytest.mark.integracion

CLAVE_ANONIMA = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9"
    ".CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0"
)
FECHA = "2026-10-28T12:00:00-03:00"


def _supabase_disponible() -> bool:
    try:
        return httpx.get(f"{configuracion().supabase_url}/auth/v1/health", timeout=2).status_code == 200
    except httpx.HTTPError:
        return False


if not _supabase_disponible():
    pytest.skip("Supabase local no está corriendo", allow_module_level=True)


def _crear_cuenta(nombre: str) -> dict[str, str]:
    respuesta = httpx.post(
        f"{configuracion().supabase_url}/auth/v1/signup",
        headers={"apikey": CLAVE_ANONIMA},
        json={
            "email": f"{nombre}-{uuid4().hex[:8]}@ejemplo.com",
            "password": "clave-de-prueba",
            "data": {"nombre": nombre},
        },
        timeout=10,
    )
    respuesta.raise_for_status()
    return {"Authorization": f"Bearer {respuesta.json()['access_token']}"}


@pytest.fixture(scope="module")
def cliente():
    with TestClient(crear_app()) as cliente:
        yield cliente


@pytest.fixture(scope="module")
def ana():
    return _crear_cuenta("Ana")


@pytest.fixture(scope="module")
def beto():
    return _crear_cuenta("Beto")


def test_el_perfil_y_el_catalogo_se_crean_al_registrarse(cliente, ana):
    perfil = cliente.get("/api/perfil", headers=ana).json()
    categorias = cliente.get("/api/categorias", headers=ana).json()

    assert perfil["nombre_visible"] == "Ana"
    assert {"Supermercado", "Auto", "Sueldo"} <= {c["nombre"] for c in categorias}


def test_flujo_completo_con_gasto_dividido(cliente, ana):
    auto = next(c for c in cliente.get("/api/categorias", headers=ana).json() if c["nombre"] == "Auto")
    assert (
        cliente.post(
            "/api/movimientos/ingresos", headers=ana, json={"monto": "1250000", "ocurrido_en": FECHA}
        ).status_code
        == 201
    )
    viaje = cliente.post(
        "/api/objetivos", headers=ana, json={"nombre": "Viaje", "monto_meta": "800000"}
    ).json()
    for desde, hacia, monto in [
        ({"bolsillo": "disponible"}, {"bolsillo": "ahorros"}, "400000"),
        ({"bolsillo": "ahorros"}, {"bolsillo": "ahorros", "objetivo_id": viaje["id"]}, "100000"),
    ]:
        respuesta = cliente.post(
            "/api/movimientos/transferencias",
            headers=ana,
            json={"monto": monto, "ocurrido_en": FECHA, "desde": desde, "hacia": hacia},
        )
        assert respuesta.status_code == 201, respuesta.text

    gasto = cliente.post(
        "/api/movimientos/gastos",
        headers=ana,
        json={
            "monto": "100000",
            "ocurrido_en": FECHA,
            "categoria_id": auto["id"],
            "descripcion": "Arreglo del auto",
            "origenes": [
                {"bolsillo": "disponible", "monto": "50000"},
                {"bolsillo": "ahorros", "monto": "30000"},
                {"bolsillo": "ahorros", "objetivo_id": viaje["id"], "monto": "20000"},
            ],
        },
    )

    assert gasto.status_code == 201, gasto.text
    resumen = cliente.get("/api/resumen", headers=ana, params={"mes": "2026-10"}).json()
    assert resumen["saldos"] == {
        "total": "1150000.00",
        "disponible": "800000.00",
        "ahorros": "350000.00",
        "ahorro_libre": "270000.00",
    }
    assert (resumen["ingresos_mes"], resumen["gastos_mes"]) == ("1250000.00", "100000.00")
    assert resumen["objetivos"][0]["apartado"] == "80000.00"


def test_gasto_sin_saldo_se_rechaza_y_no_se_guarda(cliente, ana):
    antes = cliente.get("/api/movimientos", headers=ana).json()

    respuesta = cliente.post(
        "/api/movimientos/gastos", headers=ana, json={"monto": "99999999", "ocurrido_en": FECHA}
    )

    assert respuesta.status_code == 409
    assert len(cliente.get("/api/movimientos", headers=ana).json()) == len(antes)


def test_una_cuenta_no_ve_ni_usa_los_datos_de_la_otra(cliente, ana, beto):
    objetivo_de_ana = cliente.get("/api/objetivos", headers=ana).json()[0]
    movimiento_de_ana = cliente.get("/api/movimientos", headers=ana).json()[0]

    assert cliente.get("/api/movimientos", headers=beto).json() == []
    assert cliente.get("/api/objetivos", headers=beto).json() == []
    assert cliente.delete(f"/api/movimientos/{movimiento_de_ana['id']}", headers=beto).status_code == 404
    cliente.post("/api/movimientos/ingresos", headers=beto, json={"monto": "1000", "ocurrido_en": FECHA})
    respuesta = cliente.post(
        "/api/movimientos/gastos",
        headers=beto,
        json={
            "monto": "10",
            "ocurrido_en": FECHA,
            "origenes": [{"bolsillo": "ahorros", "objetivo_id": objetivo_de_ana["id"], "monto": "10"}],
        },
    )
    assert respuesta.status_code == 404
    assert (
        cliente.get("/api/resumen", headers=beto, params={"mes": "2026-10"}).json()["saldos"]["total"]
        == "1000.00"
    )
