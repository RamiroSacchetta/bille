"""Tests de dólares (S1–S6 de odd/tasks/dolares.md).

Los dólares son un bolsillo aparte que nunca se convierte: comprar y vender son cambios (no ingresos ni gastos),
"ya los tenía" es un ingreso en dólares, y los gastos y objetivos en dólares no se mezclan con los pesos.
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
from app.aplicacion.exportar import BOM, movimientos_a_csv
from app.dominio.errores import DatosInvalidos, SaldoInsuficiente
from app.dominio.modelos import (
    AHORRO_LIBRE,
    DISPONIBLE,
    DOLARES_LIBRES,
    Bolsillo,
    Moneda,
    OperacionCambio,
    TipoMovimiento,
    Ubicacion,
)
from app.dominio.puertos import FiltroMovimientos
from app.main import crear_app
from tests.memoria import AlmacenEnMemoria

AHORA = datetime(2026, 10, 28, 12, tzinfo=UTC)
INICIO_MES = datetime(2026, 10, 1, tzinfo=UTC)
FIN_MES = datetime(2026, 11, 1, tzinfo=UTC)
HOY = date(2026, 10, 28)
COMPRA, VENTA = OperacionCambio.COMPRA, OperacionCambio.VENTA


def D(valor) -> Decimal:
    return Decimal(str(valor))


@pytest.fixture
def almacen():
    return AlmacenEnMemoria()


@pytest.fixture
def usuario(almacen):
    usuario = uuid4()
    cu.registrar_ingreso(almacen, usuario, D(2_000_000), AHORA)
    return usuario


def _resumen(almacen, usuario):
    return cu.consultar_resumen(almacen, usuario, INICIO_MES, FIN_MES, HOY)


# -- Comprar y vender (S2, S4) -------------------------------------------------


def test_comprar_dolares_con_la_plata_del_mes_es_un_cambio(almacen, usuario):
    cambio = cu.cambiar(almacen, usuario, COMPRA, D(1000), D(1_200_000), AHORA)

    assert (cambio.tipo, cambio.monto, cambio.moneda) == (TipoMovimiento.CAMBIO, D(1000), Moneda.USD)
    assert {(p.ubicacion, p.monto) for p in cambio.partes} == {
        (DISPONIBLE, D(-1_200_000)),
        (DOLARES_LIBRES, D(1000)),
    }
    saldos = almacen.saldos(usuario)
    assert (saldos.disponible, saldos.total, saldos.dolares, saldos.dolares_libres) == (
        D(800_000),
        D(800_000),
        D(1000),
        D(1000),
    )


def test_comprar_dolares_con_ahorros(almacen, usuario):
    cu.transferir(almacen, usuario, D(500_000), AHORA, DISPONIBLE, AHORRO_LIBRE)

    cu.cambiar(almacen, usuario, COMPRA, D(300), D(360_000), AHORA, pesos_en=AHORRO_LIBRE)

    saldos = almacen.saldos(usuario)
    assert (saldos.disponible, saldos.ahorros, saldos.dolares) == (D(1_500_000), D(140_000), D(300))


def test_vender_dolares_suma_pesos_a_la_plata_del_mes(almacen, usuario):
    cu.cambiar(almacen, usuario, COMPRA, D(1000), D(1_200_000), AHORA)

    venta = cu.cambiar(almacen, usuario, VENTA, D(200), D(250_000), AHORA)

    assert {(p.ubicacion, p.monto) for p in venta.partes} == {
        (DOLARES_LIBRES, D(-200)),
        (DISPONIBLE, D(250_000)),
    }
    saldos = almacen.saldos(usuario)
    assert (saldos.disponible, saldos.dolares) == (D(1_050_000), D(800))


def test_comprar_y_vender_no_cuentan_como_ingreso_ni_gasto_del_mes(almacen, usuario):
    cu.cambiar(almacen, usuario, COMPRA, D(1000), D(1_200_000), AHORA)
    cu.cambiar(almacen, usuario, VENTA, D(100), D(125_000), AHORA)

    resumen = _resumen(almacen, usuario)

    assert (resumen.ingresos_periodo, resumen.gastos_periodo, resumen.gastos_dolares_periodo) == (
        D(2_000_000),
        D(0),
        D(0),
    )


def test_no_se_venden_dolares_que_no_tenes(almacen, usuario):
    cu.cambiar(almacen, usuario, COMPRA, D(100), D(120_000), AHORA)

    with pytest.raises(SaldoInsuficiente, match="dólares libres"):
        cu.cambiar(almacen, usuario, VENTA, D(150), D(180_000), AHORA)


def test_no_se_compran_dolares_sin_pesos(almacen, usuario):
    with pytest.raises(SaldoInsuficiente, match="plata del mes"):
        cu.cambiar(almacen, usuario, COMPRA, D(5000), D(6_000_000), AHORA)


def test_los_pesos_del_cambio_tienen_que_estar_en_pesos(almacen, usuario):
    with pytest.raises(DatosInvalidos, match="pesos"):
        cu.cambiar(almacen, usuario, COMPRA, D(100), D(120_000), AHORA, pesos_en=DOLARES_LIBRES)


# -- Ya los tenía (S3) --------------------------------------------------------


def test_los_dolares_que_ya_tenias_no_son_ingreso_del_mes(almacen, usuario):
    ingreso = cu.registrar_ingreso(almacen, usuario, D(3000), AHORA, destino=DOLARES_LIBRES)

    assert ingreso.moneda is Moneda.USD
    assert almacen.saldos(usuario).dolares == D(3000)
    assert _resumen(almacen, usuario).ingresos_periodo == D(2_000_000)


# -- Gastos y objetivos en dólares (S5, S6) ----------------------------------


def test_gasto_en_dolares_va_aparte_del_balance_en_pesos(almacen, usuario):
    cu.registrar_ingreso(almacen, usuario, D(1000), AHORA, destino=DOLARES_LIBRES)

    gasto = cu.registrar_gasto(almacen, usuario, D(350), AHORA, origenes=[(DOLARES_LIBRES, D(350))])

    assert gasto.moneda is Moneda.USD
    resumen = _resumen(almacen, usuario)
    assert (resumen.gastos_periodo, resumen.gastos_dolares_periodo) == (D(0), D(350))
    assert resumen.saldos.dolares == D(650)


def test_un_gasto_va_en_una_sola_moneda(almacen, usuario):
    cu.registrar_ingreso(almacen, usuario, D(1000), AHORA, destino=DOLARES_LIBRES)

    with pytest.raises(DatosInvalidos, match="Un gasto va en una sola moneda"):
        cu.registrar_gasto(
            almacen, usuario, D(200), AHORA, origenes=[(DISPONIBLE, D(100)), (DOLARES_LIBRES, D(100))]
        )


def test_no_se_gastan_dolares_que_no_tenes(almacen, usuario):
    with pytest.raises(SaldoInsuficiente, match="dólares libres"):
        cu.registrar_gasto(almacen, usuario, D(10), AHORA, origenes=[(DOLARES_LIBRES, D(10))])


def test_objetivo_en_dolares_se_aparta_desde_los_dolares(almacen, usuario):
    viaje = cu.crear_objetivo(almacen, usuario, "Viaje a Brasil", D(2000), moneda=Moneda.USD)
    cu.registrar_ingreso(almacen, usuario, D(1000), AHORA, destino=DOLARES_LIBRES)

    cu.transferir(almacen, usuario, D(300), AHORA, DOLARES_LIBRES, Ubicacion(Bolsillo.DOLARES, viaje.id))

    saldos = almacen.saldos(usuario)
    assert (saldos.dolares, saldos.dolares_libres, saldos.apartado(viaje.id)) == (D(1000), D(700), D(300))
    assert saldos.ahorro_libre == D(0)
    resumen = _resumen(almacen, usuario)
    assert [(o.objetivo.moneda, o.apartado) for o in resumen.objetivos] == [(Moneda.USD, D(300))]


def test_gasto_dividido_entre_dolares_libres_y_un_objetivo_en_dolares(almacen, usuario):
    viaje = cu.crear_objetivo(almacen, usuario, "Viaje", D(2000), moneda=Moneda.USD)
    cu.registrar_ingreso(almacen, usuario, D(1000), AHORA, destino=DOLARES_LIBRES)
    en_viaje = Ubicacion(Bolsillo.DOLARES, viaje.id)
    cu.transferir(almacen, usuario, D(500), AHORA, DOLARES_LIBRES, en_viaje)

    cu.registrar_gasto(
        almacen, usuario, D(600), AHORA, origenes=[(en_viaje, D(400)), (DOLARES_LIBRES, D(200))]
    )

    saldos = almacen.saldos(usuario)
    assert (saldos.dolares_libres, saldos.apartado(viaje.id)) == (D(300), D(100))


def test_un_objetivo_solo_acepta_su_moneda(almacen, usuario):
    viaje = cu.crear_objetivo(almacen, usuario, "Viaje", D(2000), moneda=Moneda.USD)
    auto = cu.crear_objetivo(almacen, usuario, "Auto", D(2_000_000))

    with pytest.raises(DatosInvalidos, match="El objetivo es en otra moneda"):
        cu.transferir(almacen, usuario, D(100), AHORA, DISPONIBLE, Ubicacion(Bolsillo.AHORROS, viaje.id))
    with pytest.raises(DatosInvalidos, match="El objetivo es en otra moneda"):
        cu.transferir(almacen, usuario, D(100), AHORA, DOLARES_LIBRES, Ubicacion(Bolsillo.DOLARES, auto.id))


def test_una_transferencia_no_cambia_pesos_por_dolares(almacen, usuario):
    with pytest.raises(DatosInvalidos, match="Para pasar entre pesos y dólares usá Comprar o Vender dólares"):
        cu.transferir(almacen, usuario, D(100), AHORA, DISPONIBLE, DOLARES_LIBRES)


def test_no_se_archiva_un_objetivo_en_dolares_con_plata_apartada(almacen, usuario):
    viaje = cu.crear_objetivo(almacen, usuario, "Viaje", D(2000), moneda=Moneda.USD)
    cu.registrar_ingreso(almacen, usuario, D(100), AHORA, destino=DOLARES_LIBRES)
    cu.transferir(almacen, usuario, D(100), AHORA, DOLARES_LIBRES, Ubicacion(Bolsillo.DOLARES, viaje.id))

    with pytest.raises(DatosInvalidos, match="archivar"):
        cu.actualizar_objetivo(almacen, usuario, viaje.id, archivado=True)


def test_borrar_una_compra_de_dolares_ya_gastados_se_rechaza(almacen, usuario):
    compra = cu.cambiar(almacen, usuario, COMPRA, D(100), D(120_000), AHORA)
    cu.registrar_gasto(almacen, usuario, D(80), AHORA, origenes=[(DOLARES_LIBRES, D(80))])

    with pytest.raises(SaldoInsuficiente, match="dólares libres"):
        cu.eliminar_movimiento(almacen, usuario, compra.id)


def test_el_pago_de_una_tarjeta_es_en_pesos(almacen, usuario):
    visa = ct.crear_tarjeta(almacen, usuario, "Visa", dia_cierre=25, dia_vencimiento=5)
    cu.registrar_ingreso(almacen, usuario, D(100), AHORA, destino=DOLARES_LIBRES)

    with pytest.raises(DatosInvalidos, match="en pesos"):
        ct.pagar_resumen(almacen, usuario, visa.id, D(50), AHORA, origenes=[(DOLARES_LIBRES, D(50))])


# -- CSV (S7) -------------------------------------------------------------------


def test_el_csv_muestra_la_moneda_y_el_cambio(almacen, usuario):
    cu.cambiar(almacen, usuario, COMPRA, D(1000), D(1_200_000), datetime(2026, 10, 29, 12, tzinfo=UTC))
    cu.cambiar(almacen, usuario, VENTA, D(100), D(125_000), datetime(2026, 10, 30, 12, tzinfo=UTC))

    contenido = movimientos_a_csv(
        almacen.listar_movimientos(usuario, FiltroMovimientos()),
        categorias={},
        metodos={},
        objetivos={},
        tarjetas={},
        zona_horaria="America/Argentina/Buenos_Aires",
    )

    lineas = contenido.lstrip(BOM).split("\r\n")
    assert lineas[0] == "Fecha;Tipo;Descripción;Categoría;Método de pago;Monto;Moneda;De dónde / a dónde"
    assert lineas[1] == "28/10/2026;Ingreso;;;;2000000,00;ARS;Plata del mes 2000000,00"
    assert lineas[2] == "29/10/2026;Cambio;;;;1000,00;USD;Plata del mes -1200000,00 | Dólares libres 1000,00"
    assert lineas[3] == "30/10/2026;Cambio;;;;-100,00;USD;Dólares libres -100,00 | Plata del mes 125000,00"


# -- API (S8) -----------------------------------------------------------------


@pytest.fixture
def cliente(almacen, usuario):
    app = crear_app(con_base_de_datos=False)
    app.dependency_overrides[usuario_actual] = lambda: usuario
    app.dependency_overrides[abrir_almacen] = lambda: lambda: nullcontext(almacen)
    return TestClient(app)


FECHA = "2026-10-28T12:00:00-03:00"


def test_api_compra_de_dolares_y_resumen_separado(cliente):
    compra = cliente.post(
        "/api/movimientos/cambios",
        json={"operacion": "compra", "dolares": "1000", "pesos": "1200000", "ocurrido_en": FECHA},
    )
    assert compra.status_code == 201, compra.text
    cuerpo = compra.json()
    assert (cuerpo["tipo"], cuerpo["monto"], cuerpo["moneda"]) == ("cambio", "1000.00", "USD")
    viaje = cliente.post("/api/objetivos", json={"nombre": "Viaje", "monto_meta": "2000", "moneda": "USD"})
    assert viaje.json()["moneda"] == "USD"
    cliente.post(
        "/api/movimientos/transferencias",
        json={
            "monto": "300",
            "ocurrido_en": FECHA,
            "desde": {"bolsillo": "dolares"},
            "hacia": {"bolsillo": "dolares", "objetivo_id": viaje.json()["id"]},
        },
    )
    gasto = cliente.post(
        "/api/movimientos/gastos",
        json={"monto": "50", "ocurrido_en": FECHA, "origenes": [{"bolsillo": "dolares", "monto": "50"}]},
    )
    assert gasto.json()["moneda"] == "USD"

    resumen = cliente.get("/api/resumen", params={"mes": "2026-10"}).json()

    assert resumen["saldos"] == {
        "total": "800000.00",
        "disponible": "800000.00",
        "ahorros": "0",
        "ahorro_libre": "0",
        "dolares": "950.00",
        "dolares_libres": "650.00",
    }
    assert (resumen["ingresos_mes"], resumen["gastos_mes"], resumen["gastos_dolares_mes"]) == (
        "2000000.00",
        "0",
        "50.00",
    )
    assert [(o["moneda"], o["apartado"]) for o in resumen["objetivos"]] == [("USD", "300.00")]
    assert [o["moneda"] for o in cliente.get("/api/objetivos").json()] == ["USD"]


def test_api_venta_sin_dolares_responde_409(cliente):
    respuesta = cliente.post(
        "/api/movimientos/cambios",
        json={"operacion": "venta", "dolares": "10", "pesos": "12000", "ocurrido_en": FECHA},
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["detail"] == "No te alcanzan los dólares libres para este movimiento"


def test_api_gasto_con_dos_monedas_responde_422(cliente):
    respuesta = cliente.post(
        "/api/movimientos/gastos",
        json={
            "monto": "20",
            "ocurrido_en": FECHA,
            "origenes": [{"bolsillo": "disponible", "monto": "10"}, {"bolsillo": "dolares", "monto": "10"}],
        },
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["detail"] == "Un gasto va en una sola moneda"


def test_api_el_objetivo_en_pesos_es_el_de_siempre(cliente):
    objetivo = cliente.post("/api/objetivos", json={"nombre": "Auto", "monto_meta": "100"}).json()

    assert objetivo["moneda"] == "ARS"
