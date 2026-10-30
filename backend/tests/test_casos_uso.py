"""Tests de los casos de uso con el almacén en memoria.

Cubren las reglas pedidas: gasto pagado con ahorros (S5), que cuenta en el balance del mes (S6),
pago dividido entre plata del mes, ahorro libre y objetivos (S7) y cuentas separadas (S1).
"""

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.aplicacion import casos_uso as cu
from app.dominio.errores import DatosInvalidos, NoEncontrado, SaldoInsuficiente
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
from tests.memoria import AlmacenEnMemoria

AHORA = datetime(2026, 10, 28, 12, 0, tzinfo=UTC)
INICIO_MES = datetime(2026, 10, 1, tzinfo=UTC)
FIN_MES = datetime(2026, 11, 1, tzinfo=UTC)


def D(valor: str | int) -> Decimal:
    return Decimal(str(valor))


@pytest.fixture
def almacen() -> AlmacenEnMemoria:
    return AlmacenEnMemoria()


@pytest.fixture
def usuario():
    return uuid4()


@pytest.fixture
def con_plata(almacen, usuario):
    """Usuario con sueldo de 1.250.000, 475.000 de ahorro libre y 300.000 apartados para el viaje."""
    cu.registrar_ingreso(almacen, usuario, D(1_250_000), AHORA)
    viaje = cu.crear_objetivo(almacen, usuario, "Viaje a Bariloche", D(800_000))
    cu.transferir(almacen, usuario, D(775_000), AHORA, DISPONIBLE, AHORRO_LIBRE)
    cu.transferir(almacen, usuario, D(300_000), AHORA, AHORRO_LIBRE, Ubicacion(Bolsillo.AHORROS, viaje.id))
    return viaje


def test_ingreso_suma_a_la_plata_del_mes(almacen, usuario):
    cu.registrar_ingreso(almacen, usuario, D(1000), AHORA)

    saldos = almacen.saldos(usuario)
    assert saldos.disponible == D(1000)
    assert saldos.ahorros == 0


def test_gasto_sin_origenes_sale_de_la_plata_del_mes(almacen, usuario):
    cu.registrar_ingreso(almacen, usuario, D(1000), AHORA)

    gasto = cu.registrar_gasto(almacen, usuario, D(400), AHORA)

    assert [p.ubicacion for p in gasto.partes] == [DISPONIBLE]
    assert almacen.saldos(usuario).disponible == D(600)


def test_mandar_a_ahorros_no_cambia_el_total_ni_es_gasto(almacen, usuario):
    cu.registrar_ingreso(almacen, usuario, D(1000), AHORA)

    cu.transferir(almacen, usuario, D(300), AHORA, DISPONIBLE, AHORRO_LIBRE)

    saldos = almacen.saldos(usuario)
    assert (saldos.disponible, saldos.ahorros, saldos.total) == (D(700), D(300), D(1000))
    assert almacen.totales_periodo(usuario, INICIO_MES, FIN_MES) == (D(1000), D(0))


def test_apartar_para_objetivo_baja_el_ahorro_libre(almacen, usuario, con_plata):
    saldos = almacen.saldos(usuario)

    assert saldos.ahorros == D(775_000)
    assert saldos.apartados[con_plata.id] == D(300_000)
    assert saldos.ahorro_libre == D(475_000)


def test_gasto_dividido_entre_mes_ahorro_libre_y_objetivo(almacen, usuario, con_plata):
    # Arreglo del auto: 50.000 de la plata del mes, 30.000 del ahorro libre y 20.000 del viaje
    viaje = Ubicacion(Bolsillo.AHORROS, con_plata.id)
    antes = almacen.saldos(usuario)

    gasto = cu.registrar_gasto(
        almacen,
        usuario,
        D(100_000),
        AHORA,
        descripcion="Arreglo del auto",
        origenes=[(DISPONIBLE, D(50_000)), (AHORRO_LIBRE, D(30_000)), (viaje, D(20_000))],
    )

    despues = almacen.saldos(usuario)
    assert gasto.monto == D(100_000)
    assert despues.total == antes.total - D(100_000)
    assert despues.disponible == antes.disponible - D(50_000)
    assert despues.ahorros == antes.ahorros - D(50_000)
    assert despues.ahorro_libre == antes.ahorro_libre - D(30_000)
    assert despues.apartados[con_plata.id] == antes.apartados[con_plata.id] - D(20_000)


def test_gasto_pagado_con_ahorros_cuenta_en_el_balance_del_mes(almacen, usuario, con_plata):
    cu.registrar_gasto(almacen, usuario, D(60_000), AHORA, origenes=[(AHORRO_LIBRE, D(60_000))])

    ingresos, gastos = almacen.totales_periodo(usuario, INICIO_MES, FIN_MES)
    assert (ingresos, gastos) == (D(1_250_000), D(60_000))


def test_gasto_dividido_que_no_suma_el_total_se_rechaza(almacen, usuario, con_plata):
    with pytest.raises(DatosInvalidos, match="sumar el total"):
        cu.registrar_gasto(
            almacen, usuario, D(100_000), AHORA, origenes=[(DISPONIBLE, D(50_000)), (AHORRO_LIBRE, D(40_000))]
        )


def test_origen_repetido_se_rechaza(almacen, usuario, con_plata):
    with pytest.raises(DatosInvalidos, match="una sola vez"):
        cu.registrar_gasto(
            almacen, usuario, D(100), AHORA, origenes=[(DISPONIBLE, D(50)), (DISPONIBLE, D(50))]
        )


@pytest.mark.parametrize(
    ("origen", "mensaje"),
    [("mes", "plata del mes"), ("libre", "ahorro libre"), ("objetivo", "apartado en el objetivo")],
)
def test_no_se_puede_gastar_mas_de_lo_que_hay(almacen, usuario, con_plata, origen, mensaje):
    ubicaciones = {
        "mes": DISPONIBLE,
        "libre": AHORRO_LIBRE,
        "objetivo": Ubicacion(Bolsillo.AHORROS, con_plata.id),
    }
    with pytest.raises(SaldoInsuficiente, match=mensaje):
        cu.registrar_gasto(
            almacen, usuario, D(5_000_000), AHORA, origenes=[(ubicaciones[origen], D(5_000_000))]
        )
    assert almacen.bloqueos, "Debe bloquear al usuario antes de validar saldos"


def test_categoria_de_otro_tipo_se_rechaza(almacen, usuario):
    sueldo = almacen.agregar_categoria(usuario, "Sueldo", TipoMovimiento.INGRESO)
    cu.registrar_ingreso(almacen, usuario, D(100), AHORA)

    with pytest.raises(DatosInvalidos, match="no es de gasto"):
        cu.registrar_gasto(almacen, usuario, D(10), AHORA, categoria_id=sueldo)


def test_no_se_puede_usar_categoria_ni_objetivo_de_otro_usuario(almacen, usuario, con_plata):
    otro = uuid4()
    categoria_ajena = almacen.agregar_categoria(otro, "Auto", TipoMovimiento.GASTO)

    with pytest.raises(NoEncontrado, match="categoría"):
        cu.registrar_gasto(almacen, usuario, D(10), AHORA, categoria_id=categoria_ajena)
    with pytest.raises(NoEncontrado, match="objetivo"):
        cu.registrar_gasto(
            almacen, otro, D(10), AHORA, origenes=[(Ubicacion(Bolsillo.AHORROS, con_plata.id), D(10))]
        )


def test_monto_invalido_se_rechaza(almacen, usuario):
    with pytest.raises(DatosInvalidos, match="mayor a cero"):
        cu.registrar_ingreso(almacen, usuario, D(0), AHORA)
    with pytest.raises(DatosInvalidos, match="dos decimales"):
        cu.registrar_ingreso(almacen, usuario, D("10.555"), AHORA)


def test_transferencia_al_mismo_lugar_se_rechaza(almacen, usuario):
    with pytest.raises(DatosInvalidos, match="distintos"):
        cu.transferir(almacen, usuario, D(10), AHORA, DISPONIBLE, DISPONIBLE)


def test_eliminar_movimiento_revierte_sus_partes(almacen, usuario):
    cu.registrar_ingreso(almacen, usuario, D(1000), AHORA)
    gasto = cu.registrar_gasto(almacen, usuario, D(400), AHORA)

    cu.eliminar_movimiento(almacen, usuario, gasto.id)

    assert almacen.saldos(usuario).disponible == D(1000)


def test_no_se_puede_eliminar_un_ingreso_ya_gastado(almacen, usuario):
    ingreso = cu.registrar_ingreso(almacen, usuario, D(1000), AHORA)
    cu.registrar_gasto(almacen, usuario, D(800), AHORA)

    with pytest.raises(SaldoInsuficiente):
        cu.eliminar_movimiento(almacen, usuario, ingreso.id)


def test_no_se_puede_archivar_objetivo_con_plata_apartada(almacen, usuario, con_plata):
    with pytest.raises(DatosInvalidos, match="Devolvé lo apartado"):
        cu.actualizar_objetivo(almacen, usuario, con_plata.id, archivado=True)


def test_eliminar_objetivo_devuelve_lo_apartado_al_ahorro_libre_y_lo_archiva(almacen, usuario, con_plata):
    cu.eliminar_objetivo(almacen, usuario, con_plata.id, AHORA)

    saldos = almacen.saldos(usuario)
    assert (saldos.ahorros, saldos.ahorro_libre) == (D(775_000), D(775_000))
    assert saldos.apartado(con_plata.id) == 0
    assert almacen.obtener_objetivo(usuario, con_plata.id).archivado
    assert [
        o.objetivo
        for o in cu.consultar_resumen(almacen, usuario, INICIO_MES, FIN_MES, INICIO_MES.date()).objetivos
    ] == []


def test_eliminar_objetivo_en_dolares_devuelve_a_los_dolares_libres(almacen, usuario):
    cu.registrar_ingreso(almacen, usuario, D(1_200_000), AHORA)
    cu.cambiar(almacen, usuario, OperacionCambio.COMPRA, D(1000), D(1_200_000), AHORA)
    viaje = cu.crear_objetivo(almacen, usuario, "Viaje", D(2000), moneda=Moneda.USD)
    cu.transferir(almacen, usuario, D(400), AHORA, DOLARES_LIBRES, Ubicacion(Bolsillo.DOLARES, viaje.id))

    cu.eliminar_objetivo(almacen, usuario, viaje.id, AHORA)

    saldos = almacen.saldos(usuario)
    assert (saldos.dolares, saldos.dolares_libres, saldos.ahorros) == (D(1000), D(1000), D(0))
    assert almacen.obtener_objetivo(usuario, viaje.id).archivado


def test_eliminar_objetivo_sin_movimientos_lo_borra(almacen, usuario):
    objetivo = cu.crear_objetivo(almacen, usuario, "Auto", D(1000))

    cu.eliminar_objetivo(almacen, usuario, objetivo.id, AHORA)

    assert almacen.obtener_objetivo(usuario, objetivo.id) is None
    assert almacen.movimientos == {}


def test_editar_objetivo_cambia_nombre_y_meta_sin_tocar_la_fecha(almacen, usuario):
    objetivo = cu.crear_objetivo(almacen, usuario, "Auto", D(1000), date(2027, 1, 1))

    cu.actualizar_objetivo(almacen, usuario, objetivo.id, nombre=" Moto ", monto_meta=D(500))

    editado = almacen.obtener_objetivo(usuario, objetivo.id)
    assert (editado.nombre, editado.monto_meta, editado.fecha_meta) == ("Moto", D(500), date(2027, 1, 1))


def test_editar_objetivo_con_fecha_vacia_la_borra(almacen, usuario):
    objetivo = cu.crear_objetivo(almacen, usuario, "Auto", D(1000), date(2027, 1, 1))

    cu.actualizar_objetivo(almacen, usuario, objetivo.id, fecha_meta=None)

    assert almacen.obtener_objetivo(usuario, objetivo.id).fecha_meta is None


def test_resumen_del_inicio(almacen, usuario, con_plata):
    cu.registrar_gasto(
        almacen, usuario, D(100_000), AHORA, origenes=[(DISPONIBLE, D(50_000)), (AHORRO_LIBRE, D(50_000))]
    )

    resumen = cu.consultar_resumen(almacen, usuario, INICIO_MES, FIN_MES, INICIO_MES.date())

    assert resumen.saldos.total == D(1_150_000)
    assert (resumen.ingresos_periodo, resumen.gastos_periodo) == (D(1_250_000), D(100_000))
    assert [(o.objetivo.nombre, o.apartado) for o in resumen.objetivos] == [("Viaje a Bariloche", D(300_000))]


def test_los_datos_de_un_usuario_no_afectan_al_otro(almacen, usuario, con_plata):
    otro = uuid4()

    assert almacen.saldos(otro).total == 0
    with pytest.raises(SaldoInsuficiente):
        cu.registrar_gasto(almacen, otro, D(1), AHORA)
