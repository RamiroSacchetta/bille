"""Tests del export a CSV: formato para Excel es-AR, signos, nombres y pago dividido."""

from contextlib import nullcontext
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.dependencias import abrir_almacen, usuario_actual
from app.aplicacion import casos_uso as cu
from app.aplicacion.exportar import BOM, movimientos_a_csv, numero
from app.dominio.modelos import AHORRO_LIBRE, DISPONIBLE, Bolsillo, TipoMovimiento, Ubicacion
from app.dominio.puertos import FiltroMovimientos
from app.main import crear_app
from tests.memoria import AlmacenEnMemoria

USUARIO = uuid4()
# 28/10 a las 01:00 UTC es todavía 27/10 en Buenos Aires
FECHA = datetime(2026, 10, 28, 1, 0, tzinfo=UTC)


def test_numeros_con_coma_decimal_y_sin_miles():
    assert numero(Decimal("1250000.5")) == "1250000,50"
    assert numero(Decimal(-38420)) == "-38420,00"


def test_csv_con_encabezados_signos_nombres_y_partes():
    almacen = AlmacenEnMemoria()
    auto = almacen.agregar_categoria(USUARIO, "Auto", TipoMovimiento.GASTO)
    efectivo = almacen.agregar_metodo(USUARIO, "Efectivo")
    viaje = cu.crear_objetivo(almacen, USUARIO, "Viaje", Decimal(800_000))
    cu.registrar_ingreso(almacen, USUARIO, Decimal(1_000_000), FECHA)
    cu.transferir(
        almacen, USUARIO, Decimal(300_000), FECHA, DISPONIBLE, Ubicacion(Bolsillo.AHORROS, viaje.id)
    )
    cu.registrar_gasto(
        almacen,
        USUARIO,
        Decimal(100_000),
        FECHA,
        categoria_id=auto,
        metodo_pago_id=efectivo,
        descripcion="Arreglo del auto; urgente",
        origenes=[(DISPONIBLE, Decimal(50_000)), (Ubicacion(Bolsillo.AHORROS, viaje.id), Decimal(50_000))],
    )

    contenido = movimientos_a_csv(
        almacen.listar_movimientos(USUARIO, FiltroMovimientos()),
        categorias={auto: "Auto"},
        metodos={efectivo: "Efectivo"},
        objetivos={viaje.id: "Viaje"},
        tarjetas={},
        zona_horaria="America/Argentina/Buenos_Aires",
    )

    lineas = contenido.lstrip(BOM).split("\r\n")
    assert contenido.startswith(BOM)
    assert lineas[0] == "Fecha;Tipo;Descripción;Categoría;Método de pago;Monto;Moneda;De dónde / a dónde"
    assert lineas[1] == "27/10/2026;Ingreso;;;;1000000,00;ARS;Plata del mes 1000000,00"
    assert lineas[2] == "27/10/2026;Transferencia;;;;300000,00;ARS;Plata del mes -300000,00 | Viaje 300000,00"
    assert lineas[3] == (
        '27/10/2026;Gasto;"Arreglo del auto; urgente";Auto;Efectivo;-100000,00;ARS;'
        "Plata del mes -50000,00 | Viaje -50000,00"
    )


def test_endpoint_devuelve_un_archivo_csv():
    almacen = AlmacenEnMemoria()
    cu.registrar_ingreso(almacen, USUARIO, Decimal(1000), FECHA)
    cu.transferir(almacen, USUARIO, Decimal(100), FECHA, DISPONIBLE, AHORRO_LIBRE)
    app = crear_app(con_base_de_datos=False)
    app.dependency_overrides[usuario_actual] = lambda: USUARIO
    app.dependency_overrides[abrir_almacen] = lambda: lambda: nullcontext(almacen)

    respuesta = TestClient(app).get("/api/exportar/movimientos", params={"mes": "2026-10"})

    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith("text/csv")
    assert respuesta.headers["content-disposition"] == 'attachment; filename="bille-movimientos-2026-10.csv"'
    assert respuesta.content.decode("utf-8").count("\r\n") == 3


def test_exportar_sin_sesion_responde_401():
    respuesta = TestClient(crear_app(con_base_de_datos=False)).get("/api/exportar/movimientos")

    assert respuesta.status_code == 401
