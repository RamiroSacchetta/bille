"""Rutas de la API. Cada endpoint abre la transacción del usuario, llama al caso de uso y responde."""

from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Query, Response, status

from app.api.dependencias import Abrir, UsuarioActual
from app.api.esquemas import (
    CambioEntrada,
    CategoriaEntrada,
    CategoriaSalida,
    CompraTarjetaEntrada,
    CompraTarjetaSalida,
    GastoEntrada,
    IngresoEntrada,
    MetodoPagoCambios,
    MetodoPagoEntrada,
    MetodoPagoSalida,
    MovimientoSalida,
    ObjetivoCambios,
    ObjetivoEntrada,
    ObjetivoSalida,
    PagoResumenEntrada,
    PerfilCambios,
    PerfilSalida,
    ResumenSalida,
    TarjetaCambios,
    TarjetaEntrada,
    TarjetaSalida,
    TransferenciaEntrada,
    UbicacionEntrada,
)
from app.aplicacion import casos_uso as cu
from app.aplicacion import catalogo
from app.aplicacion import tarjetas as ct
from app.aplicacion.exportar import movimientos_a_csv
from app.config import configuracion
from app.dominio.modelos import TipoMovimiento, Ubicacion
from app.dominio.puertos import FiltroMovimientos

rutas = APIRouter(prefix="/api")

PATRON_MES = r"^\d{4}-(0[1-9]|1[0-2])$"


def _ubicacion(entrada: UbicacionEntrada) -> Ubicacion:
    return cu.ubicacion(entrada.bolsillo, entrada.objetivo_id)


def _hoy():
    return datetime.now(ZoneInfo(configuracion().zona_horaria)).date()


def _limites_mes(mes: str) -> tuple[datetime, datetime]:
    """Primer instante del mes y del mes siguiente, en la zona horaria del usuario."""
    anio, numero = (int(parte) for parte in mes.split("-"))
    zona = ZoneInfo(configuracion().zona_horaria)
    desde = datetime(anio, numero, 1, tzinfo=zona)
    hasta = datetime(anio + numero // 12, numero % 12 + 1, 1, tzinfo=zona)
    return desde, hasta


@rutas.get("/salud", tags=["sistema"])
def salud() -> dict:
    return {"estado": "ok"}


# -- Resumen ----------------------------------------------------------------


@rutas.get("/resumen", response_model=ResumenSalida, tags=["resumen"])
def resumen(usuario: UsuarioActual, abrir: Abrir, mes: str = Query(pattern=PATRON_MES)):
    desde, hasta = _limites_mes(mes)
    with abrir() as almacen:
        return ResumenSalida.desde(cu.consultar_resumen(almacen, usuario, desde, hasta, _hoy()))


# -- Movimientos ------------------------------------------------------------


@rutas.get("/movimientos", response_model=list[MovimientoSalida], tags=["movimientos"])
def listar_movimientos(
    usuario: UsuarioActual,
    abrir: Abrir,
    mes: str | None = Query(default=None, pattern=PATRON_MES),
    tipo: TipoMovimiento | None = None,
    categoria_id: UUID | None = None,
):
    desde, hasta = _limites_mes(mes) if mes else (None, None)
    filtro = FiltroMovimientos(desde=desde, hasta=hasta, tipo=tipo, categoria_id=categoria_id)
    with abrir() as almacen:
        return [MovimientoSalida.desde(m) for m in almacen.listar_movimientos(usuario, filtro)]


@rutas.post("/movimientos/ingresos", response_model=MovimientoSalida, status_code=201, tags=["movimientos"])
def registrar_ingreso(datos: IngresoEntrada, usuario: UsuarioActual, abrir: Abrir):
    with abrir() as almacen:
        movimiento = cu.registrar_ingreso(
            almacen,
            usuario,
            datos.monto,
            datos.ocurrido_en,
            categoria_id=datos.categoria_id,
            metodo_pago_id=datos.metodo_pago_id,
            descripcion=datos.descripcion,
            destino=_ubicacion(datos.destino),
            id_carga=datos.id_carga,
        )
    return MovimientoSalida.desde(movimiento)


@rutas.post("/movimientos/gastos", response_model=MovimientoSalida, status_code=201, tags=["movimientos"])
def registrar_gasto(datos: GastoEntrada, usuario: UsuarioActual, abrir: Abrir):
    origenes = [(_ubicacion(o), o.monto) for o in datos.origenes] if datos.origenes else None
    with abrir() as almacen:
        movimiento = cu.registrar_gasto(
            almacen,
            usuario,
            datos.monto,
            datos.ocurrido_en,
            categoria_id=datos.categoria_id,
            metodo_pago_id=datos.metodo_pago_id,
            descripcion=datos.descripcion,
            origenes=origenes,
            id_carga=datos.id_carga,
        )
    return MovimientoSalida.desde(movimiento)


@rutas.post(
    "/movimientos/transferencias", response_model=MovimientoSalida, status_code=201, tags=["movimientos"]
)
def transferir(datos: TransferenciaEntrada, usuario: UsuarioActual, abrir: Abrir):
    with abrir() as almacen:
        movimiento = cu.transferir(
            almacen,
            usuario,
            datos.monto,
            datos.ocurrido_en,
            _ubicacion(datos.desde),
            _ubicacion(datos.hacia),
            descripcion=datos.descripcion,
        )
    return MovimientoSalida.desde(movimiento)


@rutas.post("/movimientos/cambios", response_model=MovimientoSalida, status_code=201, tags=["movimientos"])
def cambiar(datos: CambioEntrada, usuario: UsuarioActual, abrir: Abrir):
    with abrir() as almacen:
        movimiento = cu.cambiar(
            almacen,
            usuario,
            datos.operacion,
            datos.dolares,
            datos.pesos,
            datos.ocurrido_en,
            pesos_en=cu.ubicacion(datos.pesos_en.bolsillo),
            descripcion=datos.descripcion,
            id_carga=datos.id_carga,
        )
    return MovimientoSalida.desde(movimiento)


@rutas.delete("/movimientos/{movimiento_id}", status_code=204, tags=["movimientos"])
def eliminar_movimiento(movimiento_id: UUID, usuario: UsuarioActual, abrir: Abrir):
    with abrir() as almacen:
        cu.eliminar_movimiento(almacen, usuario, movimiento_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# -- Objetivos --------------------------------------------------------------


@rutas.get("/objetivos", response_model=list[ObjetivoSalida], tags=["objetivos"])
def listar_objetivos(usuario: UsuarioActual, abrir: Abrir):
    with abrir() as almacen:
        saldos = almacen.saldos(usuario)
        return [ObjetivoSalida.desde(o, saldos.apartado(o.id)) for o in almacen.listar_objetivos(usuario)]


@rutas.post("/objetivos", response_model=ObjetivoSalida, status_code=201, tags=["objetivos"])
def crear_objetivo(datos: ObjetivoEntrada, usuario: UsuarioActual, abrir: Abrir):
    with abrir() as almacen:
        objetivo = cu.crear_objetivo(
            almacen, usuario, datos.nombre, datos.monto_meta, datos.fecha_meta, moneda=datos.moneda
        )
    return ObjetivoSalida.desde(objetivo, Decimal(0))


@rutas.patch("/objetivos/{objetivo_id}", response_model=ObjetivoSalida, tags=["objetivos"])
def actualizar_objetivo(objetivo_id: UUID, datos: ObjetivoCambios, usuario: UsuarioActual, abrir: Abrir):
    with abrir() as almacen:
        objetivo = cu.actualizar_objetivo(
            almacen, usuario, objetivo_id, **datos.model_dump(exclude_unset=True)
        )
        apartado = almacen.saldos(usuario).apartado(objetivo_id)
    return ObjetivoSalida.desde(objetivo, apartado)


@rutas.delete("/objetivos/{objetivo_id}", status_code=204, tags=["objetivos"])
def eliminar_objetivo(objetivo_id: UUID, usuario: UsuarioActual, abrir: Abrir):
    with abrir() as almacen:
        cu.eliminar_objetivo(almacen, usuario, objetivo_id, datetime.now(UTC))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# -- Catálogo ---------------------------------------------------------------


@rutas.get("/perfil", response_model=PerfilSalida, tags=["catálogo"])
def obtener_perfil(usuario: UsuarioActual, abrir: Abrir):
    with abrir() as almacen:
        return asdict(catalogo.obtener_perfil(almacen, usuario))


@rutas.patch("/perfil", response_model=PerfilSalida, tags=["catálogo"])
def actualizar_perfil(datos: PerfilCambios, usuario: UsuarioActual, abrir: Abrir):
    with abrir() as almacen:
        return asdict(catalogo.actualizar_perfil(almacen, usuario, **datos.model_dump(exclude_unset=True)))


@rutas.get("/categorias", response_model=list[CategoriaSalida], tags=["catálogo"])
def listar_categorias(usuario: UsuarioActual, abrir: Abrir):
    with abrir() as almacen:
        return [asdict(c) for c in almacen.listar_categorias(usuario)]


@rutas.post("/categorias", response_model=CategoriaSalida, status_code=201, tags=["catálogo"])
def crear_categoria(datos: CategoriaEntrada, usuario: UsuarioActual, abrir: Abrir):
    with abrir() as almacen:
        return asdict(catalogo.crear_categoria(almacen, usuario, datos.nombre, datos.tipo, datos.icono))


@rutas.delete("/categorias/{categoria_id}", status_code=204, tags=["catálogo"])
def eliminar_categoria(categoria_id: UUID, usuario: UsuarioActual, abrir: Abrir):
    with abrir() as almacen:
        catalogo.eliminar_categoria(almacen, usuario, categoria_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@rutas.get("/metodos-pago", response_model=list[MetodoPagoSalida], tags=["catálogo"])
def listar_metodos_pago(usuario: UsuarioActual, abrir: Abrir):
    with abrir() as almacen:
        return [asdict(m) for m in almacen.listar_metodos_pago(usuario)]


@rutas.post("/metodos-pago", response_model=MetodoPagoSalida, status_code=201, tags=["catálogo"])
def crear_metodo_pago(datos: MetodoPagoEntrada, usuario: UsuarioActual, abrir: Abrir):
    with abrir() as almacen:
        return asdict(catalogo.crear_metodo_pago(almacen, usuario, datos.nombre, datos.tipo))


@rutas.patch("/metodos-pago/{metodo_pago_id}", response_model=MetodoPagoSalida, tags=["catálogo"])
def actualizar_metodo_pago(
    metodo_pago_id: UUID, datos: MetodoPagoCambios, usuario: UsuarioActual, abrir: Abrir
):
    with abrir() as almacen:
        return asdict(catalogo.actualizar_metodo_pago(almacen, usuario, metodo_pago_id, datos.activo))


# -- Tarjetas de crédito ----------------------------------------------------


@rutas.get("/tarjetas", response_model=list[TarjetaSalida], tags=["tarjetas"])
def listar_tarjetas(usuario: UsuarioActual, abrir: Abrir):
    with abrir() as almacen:
        return [TarjetaSalida.desde(e) for e in ct.estado_tarjetas(almacen, usuario, _hoy())]


def _estado_de(almacen, usuario: UUID, tarjeta_id: UUID) -> TarjetaSalida:
    estado = next(e for e in ct.estado_tarjetas(almacen, usuario, _hoy()) if e.tarjeta.id == tarjeta_id)
    return TarjetaSalida.desde(estado)


@rutas.post("/tarjetas", response_model=TarjetaSalida, status_code=201, tags=["tarjetas"])
def crear_tarjeta(datos: TarjetaEntrada, usuario: UsuarioActual, abrir: Abrir):
    with abrir() as almacen:
        tarjeta = ct.crear_tarjeta(almacen, usuario, datos.nombre, datos.dia_cierre, datos.dia_vencimiento)
        return _estado_de(almacen, usuario, tarjeta.id)


@rutas.patch("/tarjetas/{tarjeta_id}", response_model=TarjetaSalida, tags=["tarjetas"])
def actualizar_tarjeta(tarjeta_id: UUID, datos: TarjetaCambios, usuario: UsuarioActual, abrir: Abrir):
    with abrir() as almacen:
        ct.actualizar_tarjeta(almacen, usuario, tarjeta_id, **datos.model_dump(exclude_unset=True))
        return _estado_de(almacen, usuario, tarjeta_id)


@rutas.get("/tarjetas/{tarjeta_id}/compras", response_model=list[CompraTarjetaSalida], tags=["tarjetas"])
def listar_compras(tarjeta_id: UUID, usuario: UsuarioActual, abrir: Abrir):
    with abrir() as almacen:
        return [CompraTarjetaSalida.desde(c) for c in almacen.listar_compras_tarjeta(usuario, tarjeta_id)]


@rutas.post(
    "/tarjetas/{tarjeta_id}/compras", response_model=CompraTarjetaSalida, status_code=201, tags=["tarjetas"]
)
def registrar_compra(tarjeta_id: UUID, datos: CompraTarjetaEntrada, usuario: UsuarioActual, abrir: Abrir):
    with abrir() as almacen:
        compra = ct.registrar_compra(
            almacen,
            usuario,
            tarjeta_id,
            datos.monto,
            datos.cuotas,
            datos.comprado_en,
            categoria_id=datos.categoria_id,
            descripcion=datos.descripcion,
            id_carga=datos.id_carga,
        )
    return CompraTarjetaSalida.desde(compra)


@rutas.delete("/tarjetas/compras/{compra_id}", status_code=204, tags=["tarjetas"])
def eliminar_compra(compra_id: UUID, usuario: UsuarioActual, abrir: Abrir):
    with abrir() as almacen:
        ct.eliminar_compra(almacen, usuario, compra_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@rutas.post(
    "/tarjetas/{tarjeta_id}/pagos", response_model=MovimientoSalida, status_code=201, tags=["tarjetas"]
)
def pagar_resumen(tarjeta_id: UUID, datos: PagoResumenEntrada, usuario: UsuarioActual, abrir: Abrir):
    origenes = [(_ubicacion(o), o.monto) for o in datos.origenes] if datos.origenes else None
    with abrir() as almacen:
        pago = ct.pagar_resumen(almacen, usuario, tarjeta_id, datos.monto, datos.ocurrido_en, origenes)
    return MovimientoSalida.desde(pago)


# -- Exportar ---------------------------------------------------------------


@rutas.get("/exportar/movimientos", tags=["exportar"], response_class=Response)
def exportar_movimientos(
    usuario: UsuarioActual, abrir: Abrir, mes: str | None = Query(default=None, pattern=PATRON_MES)
):
    desde, hasta = _limites_mes(mes) if mes else (None, None)
    with abrir() as almacen:
        movimientos = almacen.listar_movimientos(
            usuario, FiltroMovimientos(desde=desde, hasta=hasta, limite=100_000)
        )
        contenido = movimientos_a_csv(
            movimientos,
            categorias={c.id: c.nombre for c in almacen.listar_categorias(usuario)},
            metodos={m.id: m.nombre for m in almacen.listar_metodos_pago(usuario)},
            objetivos={o.id: o.nombre for o in almacen.listar_objetivos(usuario)},
            tarjetas={t.id: f"{t.nombre} (crédito)" for t in almacen.listar_tarjetas(usuario)},
            zona_horaria=configuracion().zona_horaria,
        )
    nombre = f"bille-movimientos-{mes or 'todos'}.csv"
    return Response(
        content=contenido.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )
