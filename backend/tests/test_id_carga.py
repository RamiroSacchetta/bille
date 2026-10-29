"""Tests del id de carga (S3 de odd/tasks/sprint-4.md).

El dispositivo manda un id con cada carga; si la misma carga llega dos veces, se devuelve lo ya guardado
en lugar de duplicarla. Aplica a ingresos, gastos, cambios de dólares y compras con tarjeta.
"""

from contextlib import nullcontext
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencias import abrir_almacen, usuario_actual
from app.aplicacion import casos_uso as cu
from app.aplicacion import tarjetas as ct
from app.dominio.modelos import OperacionCambio
from app.dominio.puertos import FiltroMovimientos
from app.main import crear_app
from tests.memoria import AlmacenEnMemoria

AHORA = datetime(2026, 10, 28, 12, tzinfo=UTC)
FECHA = "2026-10-28T12:00:00-03:00"


def D(valor) -> Decimal:
    return Decimal(str(valor))


@pytest.fixture
def almacen():
    return AlmacenEnMemoria()


@pytest.fixture
def usuario(almacen):
    usuario = uuid4()
    cu.registrar_ingreso(almacen, usuario, D(1000), AHORA)
    return usuario


def _cantidad(almacen, usuario):
    return len(almacen.listar_movimientos(usuario, FiltroMovimientos()))


def test_el_mismo_ingreso_dos_veces_se_guarda_una_sola_vez(almacen, usuario):
    id_carga = uuid4()

    primero = cu.registrar_ingreso(almacen, usuario, D(500), AHORA, id_carga=id_carga)
    segundo = cu.registrar_ingreso(almacen, usuario, D(500), AHORA, id_carga=id_carga)

    assert segundo.id == primero.id
    assert _cantidad(almacen, usuario) == 2
    assert almacen.saldos(usuario).disponible == D(1500)


def test_el_mismo_gasto_repetido_devuelve_lo_guardado_aunque_ya_no_alcance(almacen, usuario):
    id_carga = uuid4()
    primero = cu.registrar_gasto(almacen, usuario, D(800), AHORA, id_carga=id_carga)

    # El reenvío no vuelve a validar el saldo: el gasto ya está guardado
    segundo = cu.registrar_gasto(almacen, usuario, D(800), AHORA, id_carga=id_carga)

    assert segundo.id == primero.id
    assert almacen.saldos(usuario).disponible == D(200)


def test_el_mismo_cambio_dos_veces_se_guarda_una_sola_vez(almacen, usuario):
    id_carga = uuid4()

    cu.cambiar(almacen, usuario, OperacionCambio.COMPRA, D(1), D(500), AHORA, id_carga=id_carga)
    cu.cambiar(almacen, usuario, OperacionCambio.COMPRA, D(1), D(500), AHORA, id_carga=id_carga)

    assert almacen.saldos(usuario).dolares == D(1)


def test_la_misma_compra_con_tarjeta_dos_veces_se_guarda_una_sola_vez(almacen, usuario):
    visa = ct.crear_tarjeta(almacen, usuario, "Visa", dia_cierre=25, dia_vencimiento=5)
    id_carga = uuid4()

    primera = ct.registrar_compra(almacen, usuario, visa.id, D(300), 3, date(2026, 10, 10), id_carga=id_carga)
    segunda = ct.registrar_compra(almacen, usuario, visa.id, D(300), 3, date(2026, 10, 10), id_carga=id_carga)

    assert segunda.id == primera.id
    assert len(almacen.listar_compras_tarjeta(usuario, visa.id)) == 1


def test_ids_distintos_o_sin_id_son_cargas_distintas(almacen, usuario):
    cu.registrar_gasto(almacen, usuario, D(10), AHORA, id_carga=uuid4())
    cu.registrar_gasto(almacen, usuario, D(10), AHORA, id_carga=uuid4())
    cu.registrar_gasto(almacen, usuario, D(10), AHORA)
    cu.registrar_gasto(almacen, usuario, D(10), AHORA)

    assert _cantidad(almacen, usuario) == 5
    assert almacen.saldos(usuario).disponible == D(960)


def test_el_id_de_carga_de_otro_usuario_no_cuenta(almacen, usuario):
    otro = uuid4()
    cu.registrar_ingreso(almacen, otro, D(100), AHORA)
    id_carga = uuid4()

    cu.registrar_ingreso(almacen, usuario, D(5), AHORA, id_carga=id_carga)
    del_otro = cu.registrar_ingreso(almacen, otro, D(7), AHORA, id_carga=id_carga)

    assert del_otro.monto == D(7)
    assert almacen.saldos(otro).disponible == D(107)


@pytest.fixture
def cliente(almacen, usuario):
    app = crear_app(con_base_de_datos=False)
    app.dependency_overrides[usuario_actual] = lambda: usuario
    app.dependency_overrides[abrir_almacen] = lambda: lambda: nullcontext(almacen)
    return TestClient(app)


def test_api_reenviar_la_misma_carga_responde_lo_ya_guardado(cliente):
    id_carga = str(uuid4())
    cuerpo = {"monto": "100", "ocurrido_en": FECHA, "id_carga": id_carga}

    primero = cliente.post("/api/movimientos/gastos", json=cuerpo)
    segundo = cliente.post("/api/movimientos/gastos", json=cuerpo)

    assert (primero.status_code, segundo.status_code) == (201, 201)
    assert segundo.json()["id"] == primero.json()["id"]
    assert len(cliente.get("/api/movimientos").json()) == 2
