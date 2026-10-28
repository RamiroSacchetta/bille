"""Tests de la API con el almacén en memoria: contrato HTTP, códigos de error y mensajes."""

from contextlib import nullcontext
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencias import abrir_almacen, usuario_actual
from app.main import crear_app
from tests.memoria import AlmacenEnMemoria

USUARIO = uuid4()
FECHA = "2026-10-28T12:00:00-03:00"


@pytest.fixture
def almacen() -> AlmacenEnMemoria:
    return AlmacenEnMemoria()


@pytest.fixture
def cliente(almacen) -> TestClient:
    app = crear_app(con_base_de_datos=False)
    app.dependency_overrides[usuario_actual] = lambda: USUARIO
    app.dependency_overrides[abrir_almacen] = lambda: lambda: nullcontext(almacen)
    return TestClient(app)


def test_sin_token_responde_401():
    cliente = TestClient(crear_app(con_base_de_datos=False))

    respuesta = cliente.get("/api/resumen", params={"mes": "2026-10"})

    assert respuesta.status_code == 401
    assert respuesta.json()["detail"] == "Iniciá sesión para continuar"


def test_token_invalido_responde_401():
    cliente = TestClient(crear_app(con_base_de_datos=False))

    respuesta = cliente.get(
        "/api/resumen", params={"mes": "2026-10"}, headers={"Authorization": "Bearer nada"}
    )

    assert respuesta.status_code == 401


def test_flujo_de_ingreso_ahorro_objetivo_y_gasto_dividido(cliente):
    assert (
        cliente.post("/api/movimientos/ingresos", json={"monto": "1250000", "ocurrido_en": FECHA}).status_code
        == 201
    )
    viaje = cliente.post(
        "/api/objetivos", json={"nombre": "Viaje a Bariloche", "monto_meta": "800000"}
    ).json()
    cliente.post(
        "/api/movimientos/transferencias",
        json={
            "monto": "300000",
            "ocurrido_en": FECHA,
            "desde": {"bolsillo": "disponible"},
            "hacia": {"bolsillo": "ahorros"},
        },
    )
    cliente.post(
        "/api/movimientos/transferencias",
        json={
            "monto": "100000",
            "ocurrido_en": FECHA,
            "desde": {"bolsillo": "ahorros"},
            "hacia": {"bolsillo": "ahorros", "objetivo_id": viaje["id"]},
        },
    )

    gasto = cliente.post(
        "/api/movimientos/gastos",
        json={
            "monto": "100000",
            "ocurrido_en": FECHA,
            "descripcion": "Arreglo del auto",
            "origenes": [
                {"bolsillo": "disponible", "monto": "50000"},
                {"bolsillo": "ahorros", "monto": "30000"},
                {"bolsillo": "ahorros", "objetivo_id": viaje["id"], "monto": "20000"},
            ],
        },
    )

    assert gasto.status_code == 201
    assert [p["monto"] for p in gasto.json()["partes"]] == ["-50000.00", "-30000.00", "-20000.00"]
    resumen = cliente.get("/api/resumen", params={"mes": "2026-10"}).json()
    assert resumen["saldos"] == {
        "total": "1150000.00",
        "disponible": "900000.00",
        "ahorros": "250000.00",
        "ahorro_libre": "170000.00",
    }
    assert (resumen["ingresos_mes"], resumen["gastos_mes"]) == ("1250000.00", "100000.00")
    assert resumen["objetivos"][0]["apartado"] == "80000.00"


def test_gasto_sin_plata_responde_409_con_mensaje(cliente):
    respuesta = cliente.post("/api/movimientos/gastos", json={"monto": "100", "ocurrido_en": FECHA})

    assert respuesta.status_code == 409
    assert respuesta.json()["detail"] == "No te alcanza la plata del mes para este movimiento"


def test_gasto_dividido_descuadrado_responde_422(cliente):
    cliente.post("/api/movimientos/ingresos", json={"monto": "1000", "ocurrido_en": FECHA})

    respuesta = cliente.post(
        "/api/movimientos/gastos",
        json={"monto": "500", "ocurrido_en": FECHA, "origenes": [{"bolsillo": "disponible", "monto": "400"}]},
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["detail"] == "Las partes del pago tienen que sumar el total del gasto"


def test_objetivo_en_disponible_responde_422(cliente):
    respuesta = cliente.post(
        "/api/movimientos/ingresos",
        json={
            "monto": "10",
            "ocurrido_en": FECHA,
            "destino": {"bolsillo": "disponible", "objetivo_id": str(uuid4())},
        },
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["detail"] == "Un objetivo solo puede estar dentro de ahorros"


def test_mes_invalido_responde_422(cliente):
    assert cliente.get("/api/resumen", params={"mes": "2026-13"}).status_code == 422


def test_eliminar_movimiento_inexistente_responde_404(cliente):
    respuesta = cliente.delete(f"/api/movimientos/{uuid4()}")

    assert respuesta.status_code == 404
    assert respuesta.json()["detail"] == "El movimiento no existe"


def test_listar_movimientos_del_mes(cliente):
    cliente.post("/api/movimientos/ingresos", json={"monto": "1000", "ocurrido_en": FECHA})

    respuesta = cliente.get("/api/movimientos", params={"mes": "2026-10"})

    assert respuesta.status_code == 200
    assert [m["tipo"] for m in respuesta.json()] == ["ingreso"]


@pytest.mark.parametrize(
    ("origen", "permitido"),
    [
        ("http://192.168.0.15:4200", True),
        ("http://127.0.0.1:8080", True),
        ("http://10.0.0.7:4200", True),
        ("http://172.20.1.2:4200", True),
        ("https://sitio-ajeno.com", False),
        ("http://192.168.0.15.sitio-ajeno.com", False),
    ],
)
def test_cors_acepta_solo_la_red_local(origen, permitido):
    cliente = TestClient(crear_app(con_base_de_datos=False))

    respuesta = cliente.options(
        "/api/resumen", headers={"Origin": origen, "Access-Control-Request-Method": "GET"}
    )

    assert (respuesta.headers.get("access-control-allow-origin") == origen) is permitido
