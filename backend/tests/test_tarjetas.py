"""Tests de tarjetas de crédito (S1–S4 de odd/tasks/tarjetas-credito.md).

La compra con tarjeta no mueve plata ni cuenta como gasto; solo el pago real del resumen descuenta
y baja la deuda estimada. Lo anotado es aproximado.
"""

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.aplicacion import casos_uso as cu
from app.aplicacion import tarjetas as ct
from app.dominio.errores import DatosInvalidos, NoEncontrado, SaldoInsuficiente
from app.dominio.modelos import AHORRO_LIBRE, DISPONIBLE, TipoMovimiento
from app.dominio.tarjetas import dividir_en_cuotas, mes_de_resumen
from tests.memoria import AlmacenEnMemoria

HOY = date(2026, 10, 28)
AHORA = datetime(2026, 10, 28, 12, tzinfo=UTC)
INICIO_MES = datetime(2026, 10, 1, tzinfo=UTC)
FIN_MES = datetime(2026, 11, 1, tzinfo=UTC)


def D(valor) -> Decimal:
    return Decimal(str(valor))


@pytest.fixture
def almacen():
    return AlmacenEnMemoria()


@pytest.fixture
def usuario():
    return uuid4()


@pytest.fixture
def visa(almacen, usuario):
    cu.registrar_ingreso(almacen, usuario, D(1_000_000), AHORA)
    return ct.crear_tarjeta(almacen, usuario, "Visa", dia_cierre=25, dia_vencimiento=5)


# -- Reglas puras -------------------------------------------------------------


@pytest.mark.parametrize(
    ("fecha", "esperado"),
    [
        (date(2026, 10, 25), date(2026, 10, 1)),  # el día de cierre entra en ese resumen
        (date(2026, 10, 26), date(2026, 11, 1)),  # después del cierre, al siguiente
        (date(2026, 12, 28), date(2027, 1, 1)),  # cruza el año
        (date(2026, 2, 28), date(2026, 2, 1)),  # cierre 31 en febrero: cierra el último día
    ],
)
def test_mes_de_resumen_segun_dia_de_cierre(fecha, esperado):
    dia_cierre = 31 if fecha.month == 2 else 25
    assert mes_de_resumen(fecha, dia_cierre) == esperado


def test_las_cuotas_suman_el_total_y_los_centavos_van_en_la_primera():
    cuotas = dividir_en_cuotas(D(100_000), 3, date(2026, 10, 1))

    assert [c.monto for c in cuotas] == [D("33333.34"), D("33333.33"), D("33333.33")]
    assert sum(c.monto for c in cuotas) == D(100_000)
    assert [c.mes_resumen for c in cuotas] == [date(2026, 10, 1), date(2026, 11, 1), date(2026, 12, 1)]


@pytest.mark.parametrize("cuotas", [0, 61])
def test_cantidad_de_cuotas_invalida(cuotas):
    with pytest.raises(DatosInvalidos, match="entre 1 y 60"):
        dividir_en_cuotas(D(1000), cuotas, date(2026, 10, 1))


# -- Casos de uso --------------------------------------------------------------


def test_la_compra_con_tarjeta_no_toca_tu_plata_ni_los_gastos_del_mes(almacen, usuario, visa):
    antes = almacen.saldos(usuario)

    ct.registrar_compra(almacen, usuario, visa.id, D(900_000), 3, HOY, descripcion="Heladera")

    assert almacen.saldos(usuario) == antes
    assert almacen.totales_periodo(usuario, INICIO_MES, FIN_MES) == (D(1_000_000), D(0))


def test_la_compra_se_acumula_en_cuotas_como_deuda_estimada(almacen, usuario, visa):
    ct.registrar_compra(almacen, usuario, visa.id, D(900_000), 3, date(2026, 10, 10))
    ct.registrar_compra(almacen, usuario, visa.id, D(50_000), 1, date(2026, 10, 27))

    [estado] = ct.estado_tarjetas(almacen, usuario, HOY)

    assert estado.deuda_estimada == D(950_000)
    assert estado.mes_en_curso == date(2026, 11, 1)  # hoy es 28 y la tarjeta cierra el 25
    assert estado.resumen_cerrado == D(300_000)  # la primera cuota de la heladera
    assert estado.resumen_en_curso == D(350_000)  # segunda cuota + la compra del 27
    assert estado.proximos == [(date(2026, 12, 1), D(300_000))]


def test_pagar_el_resumen_es_el_gasto_del_mes_y_baja_la_deuda(almacen, usuario, visa):
    ct.registrar_compra(almacen, usuario, visa.id, D(900_000), 3, date(2026, 10, 10))

    pago = ct.pagar_resumen(almacen, usuario, visa.id, D(320_000), AHORA)

    assert pago.tipo is TipoMovimiento.GASTO
    assert pago.tarjeta_id == visa.id
    assert pago.descripcion == "Pago de tarjeta Visa"
    assert almacen.saldos(usuario).disponible == D(680_000)
    assert almacen.totales_periodo(usuario, INICIO_MES, FIN_MES) == (D(1_000_000), D(320_000))
    assert ct.estado_tarjetas(almacen, usuario, HOY)[0].deuda_estimada == D(580_000)


def test_pagar_menos_deja_el_resto_pendiente_y_pagar_de_mas_no_da_deuda_negativa(almacen, usuario, visa):
    ct.registrar_compra(almacen, usuario, visa.id, D(100_000), 1, HOY)

    ct.pagar_resumen(almacen, usuario, visa.id, D(40_000), AHORA)
    assert ct.estado_tarjetas(almacen, usuario, HOY)[0].deuda_estimada == D(60_000)

    # Pagó más de lo anotado: se olvidó de cargar alguna compra
    ct.pagar_resumen(almacen, usuario, visa.id, D(90_000), AHORA)
    assert ct.estado_tarjetas(almacen, usuario, HOY)[0].deuda_estimada == D(0)


def test_el_pago_se_puede_dividir_con_ahorros(almacen, usuario, visa):
    cu.transferir(almacen, usuario, D(200_000), AHORA, DISPONIBLE, AHORRO_LIBRE)

    ct.pagar_resumen(
        almacen,
        usuario,
        visa.id,
        D(300_000),
        AHORA,
        origenes=[(DISPONIBLE, D(200_000)), (AHORRO_LIBRE, D(100_000))],
    )

    saldos = almacen.saldos(usuario)
    assert (saldos.disponible, saldos.ahorros) == (D(600_000), D(100_000))


def test_no_se_puede_pagar_sin_plata(almacen, usuario, visa):
    with pytest.raises(SaldoInsuficiente):
        ct.pagar_resumen(almacen, usuario, visa.id, D(2_000_000), AHORA)


def test_el_inicio_muestra_la_deuda_de_las_tarjetas(almacen, usuario, visa):
    ct.registrar_compra(almacen, usuario, visa.id, D(900_000), 3, HOY)
    ct.pagar_resumen(almacen, usuario, visa.id, D(100_000), AHORA)

    resumen = cu.consultar_resumen(almacen, usuario, INICIO_MES, FIN_MES)

    assert resumen.deuda_tarjetas == D(800_000)
    assert resumen.saldos.total == D(900_000)


def test_tarjeta_desactivada_no_acepta_compras(almacen, usuario, visa):
    ct.actualizar_tarjeta(almacen, usuario, visa.id, activa=False)

    with pytest.raises(DatosInvalidos, match="desactivada"):
        ct.registrar_compra(almacen, usuario, visa.id, D(1000), 1, HOY)


def test_no_se_puede_usar_la_tarjeta_de_otro_usuario(almacen, usuario, visa):
    otro = uuid4()
    with pytest.raises(NoEncontrado, match="tarjeta"):
        ct.registrar_compra(almacen, otro, visa.id, D(1000), 1, HOY)
    with pytest.raises(NoEncontrado, match="tarjeta"):
        ct.pagar_resumen(almacen, otro, visa.id, D(1000), AHORA)


def test_datos_invalidos_de_tarjeta(almacen, usuario):
    with pytest.raises(DatosInvalidos, match="cierre"):
        ct.crear_tarjeta(almacen, usuario, "Visa", dia_cierre=32, dia_vencimiento=5)
    with pytest.raises(DatosInvalidos, match="nombre"):
        ct.crear_tarjeta(almacen, usuario, "  ", dia_cierre=25, dia_vencimiento=5)


def test_eliminar_una_compra_baja_la_deuda(almacen, usuario, visa):
    compra = ct.registrar_compra(almacen, usuario, visa.id, D(1000), 1, HOY)

    ct.eliminar_compra(almacen, usuario, compra.id)

    assert ct.estado_tarjetas(almacen, usuario, HOY)[0].deuda_estimada == 0
