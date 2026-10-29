"""Casos de uso de Bille. Cada función recibe el almacén del usuario y aplica las reglas del dominio."""

from dataclasses import dataclass, replace
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from app.dominio import reglas
from app.dominio.errores import DatosInvalidos, NoEncontrado
from app.dominio.modelos import (
    DISPONIBLE,
    Bolsillo,
    Moneda,
    Movimiento,
    Objetivo,
    OperacionCambio,
    Saldos,
    TipoMovimiento,
    Ubicacion,
)
from app.dominio.puertos import Almacen
from app.dominio.tarjetas import calcular_estado

# ---------------------------------------------------------------------------
# Movimientos
# ---------------------------------------------------------------------------


def _validar_ubicaciones(almacen: Almacen, usuario_id: UUID, ubicaciones: list[Ubicacion]) -> None:
    for ubicacion in ubicaciones:
        if ubicacion.objetivo_id is None:
            continue
        objetivo = almacen.obtener_objetivo(usuario_id, ubicacion.objetivo_id)
        if objetivo is None:
            raise NoEncontrado("El objetivo no existe")
        if objetivo.archivado:
            raise DatosInvalidos("El objetivo está archivado")
        if objetivo.moneda is not ubicacion.moneda:
            raise DatosInvalidos("El objetivo es en otra moneda")


def _validar_categoria(
    almacen: Almacen, usuario_id: UUID, categoria_id: UUID | None, tipo: TipoMovimiento
) -> None:
    if categoria_id is None:
        return
    categoria = almacen.obtener_categoria(usuario_id, categoria_id)
    if categoria is None:
        raise NoEncontrado("La categoría no existe")
    if categoria.tipo is not tipo:
        raise DatosInvalidos(f"La categoría elegida no es de {tipo.value}")


def _validar_metodo_pago(almacen: Almacen, usuario_id: UUID, metodo_pago_id: UUID | None) -> None:
    if metodo_pago_id is not None and almacen.obtener_metodo_pago(usuario_id, metodo_pago_id) is None:
        raise NoEncontrado("El método de pago no existe")


def _guardar_con_saldos(almacen: Almacen, movimiento: Movimiento) -> Movimiento:
    """Bloquea al usuario, comprueba que ningún saldo quede negativo y guarda."""
    reglas.validar_cuadre(movimiento.tipo, movimiento.monto, movimiento.partes)
    almacen.bloquear_usuario(movimiento.usuario_id)
    reglas.validar_saldos(almacen.saldos(movimiento.usuario_id).aplicar(movimiento.partes))
    return almacen.guardar_movimiento(movimiento)


def registrar_ingreso(
    almacen: Almacen,
    usuario_id: UUID,
    monto: Decimal,
    ocurrido_en: datetime,
    categoria_id: UUID | None = None,
    metodo_pago_id: UUID | None = None,
    descripcion: str | None = None,
    destino: Ubicacion = DISPONIBLE,
) -> Movimiento:
    monto = reglas.normalizar_monto(monto)
    _validar_categoria(almacen, usuario_id, categoria_id, TipoMovimiento.INGRESO)
    _validar_metodo_pago(almacen, usuario_id, metodo_pago_id)
    _validar_ubicaciones(almacen, usuario_id, [destino])
    movimiento = Movimiento(
        usuario_id=usuario_id,
        tipo=TipoMovimiento.INGRESO,
        monto=monto,
        ocurrido_en=ocurrido_en,
        partes=reglas.partes_de_ingreso(monto, destino),
        descripcion=descripcion,
        categoria_id=categoria_id,
        metodo_pago_id=metodo_pago_id,
        moneda=destino.moneda,
    )
    return _guardar_con_saldos(almacen, movimiento)


def registrar_gasto(
    almacen: Almacen,
    usuario_id: UUID,
    monto: Decimal,
    ocurrido_en: datetime,
    categoria_id: UUID | None = None,
    metodo_pago_id: UUID | None = None,
    descripcion: str | None = None,
    origenes: list[tuple[Ubicacion, Decimal]] | None = None,
    tarjeta_id: UUID | None = None,
) -> Movimiento:
    """Sin orígenes, el gasto sale entero de la plata del mes. Con orígenes, es un pago dividido.

    La moneda del gasto es la de sus orígenes: si salen de dólares, es un gasto en dólares.
    Con `tarjeta_id` es el pago del resumen de esa tarjeta (ver aplicacion.tarjetas.pagar_resumen).
    """
    monto = reglas.normalizar_monto(monto)
    origenes = origenes or [(DISPONIBLE, monto)]
    partes = reglas.partes_de_gasto(monto, origenes)
    moneda = reglas.moneda_de(partes)
    if tarjeta_id is not None and moneda is not Moneda.ARS:
        raise DatosInvalidos("El pago de la tarjeta se hace en pesos")
    _validar_categoria(almacen, usuario_id, categoria_id, TipoMovimiento.GASTO)
    _validar_metodo_pago(almacen, usuario_id, metodo_pago_id)
    _validar_ubicaciones(almacen, usuario_id, [ubicacion for ubicacion, _ in origenes])
    movimiento = Movimiento(
        usuario_id=usuario_id,
        tipo=TipoMovimiento.GASTO,
        monto=monto,
        ocurrido_en=ocurrido_en,
        partes=partes,
        descripcion=descripcion,
        categoria_id=categoria_id,
        metodo_pago_id=metodo_pago_id,
        tarjeta_id=tarjeta_id,
        moneda=moneda,
    )
    return _guardar_con_saldos(almacen, movimiento)


def transferir(
    almacen: Almacen,
    usuario_id: UUID,
    monto: Decimal,
    ocurrido_en: datetime,
    desde: Ubicacion,
    hacia: Ubicacion,
    descripcion: str | None = None,
) -> Movimiento:
    """Mover plata propia: mandar a ahorros, pasar a disponible, apartar para un objetivo o devolver."""
    monto = reglas.normalizar_monto(monto)
    _validar_ubicaciones(almacen, usuario_id, [desde, hacia])
    movimiento = Movimiento(
        usuario_id=usuario_id,
        tipo=TipoMovimiento.TRANSFERENCIA,
        monto=monto,
        ocurrido_en=ocurrido_en,
        partes=reglas.partes_de_transferencia(monto, desde, hacia),
        descripcion=descripcion,
        moneda=desde.moneda,
    )
    return _guardar_con_saldos(almacen, movimiento)


def cambiar(
    almacen: Almacen,
    usuario_id: UUID,
    operacion: OperacionCambio,
    dolares: Decimal,
    pesos: Decimal,
    ocurrido_en: datetime,
    pesos_en: Ubicacion = DISPONIBLE,
    descripcion: str | None = None,
) -> Movimiento:
    """Comprar o vender dólares. No es ingreso ni gasto: la plata cambia de moneda.

    El monto del movimiento son los dólares; los pesos quedan en la parte en pesos, así se sabe a cuánto se cambió.
    """
    dolares = reglas.normalizar_monto(dolares)
    pesos = reglas.normalizar_monto(pesos)
    movimiento = Movimiento(
        usuario_id=usuario_id,
        tipo=TipoMovimiento.CAMBIO,
        monto=dolares,
        ocurrido_en=ocurrido_en,
        partes=reglas.partes_de_cambio(operacion, dolares, pesos, pesos_en),
        descripcion=descripcion,
        moneda=Moneda.USD,
    )
    return _guardar_con_saldos(almacen, movimiento)


def eliminar_movimiento(almacen: Almacen, usuario_id: UUID, movimiento_id: UUID) -> None:
    """Borrar un movimiento revierte sus partes; no se permite si deja algún saldo en negativo."""
    almacen.bloquear_usuario(usuario_id)
    movimiento = almacen.obtener_movimiento(usuario_id, movimiento_id)
    if movimiento is None:
        raise NoEncontrado("El movimiento no existe")
    revertidas = [replace(parte, monto=-parte.monto) for parte in movimiento.partes]
    reglas.validar_saldos(almacen.saldos(usuario_id).aplicar(revertidas))
    almacen.eliminar_movimiento(usuario_id, movimiento_id)


# ---------------------------------------------------------------------------
# Objetivos
# ---------------------------------------------------------------------------


def crear_objetivo(
    almacen: Almacen,
    usuario_id: UUID,
    nombre: str,
    monto_meta: Decimal,
    fecha_meta: date | None = None,
    moneda: Moneda = Moneda.ARS,
) -> Objetivo:
    """Un objetivo en pesos se aparta desde ahorros; uno en dólares, desde los dólares."""
    nombre = nombre.strip()
    if not nombre:
        raise DatosInvalidos("El objetivo necesita un nombre")
    objetivo = Objetivo(usuario_id, nombre, reglas.normalizar_monto(monto_meta), fecha_meta, moneda=moneda)
    return almacen.guardar_objetivo(objetivo)


def actualizar_objetivo(
    almacen: Almacen,
    usuario_id: UUID,
    objetivo_id: UUID,
    nombre: str | None = None,
    monto_meta: Decimal | None = None,
    fecha_meta: date | None = None,
    archivado: bool | None = None,
) -> Objetivo:
    objetivo = almacen.obtener_objetivo(usuario_id, objetivo_id)
    if objetivo is None:
        raise NoEncontrado("El objetivo no existe")
    if nombre is not None:
        if not nombre.strip():
            raise DatosInvalidos("El objetivo necesita un nombre")
        objetivo.nombre = nombre.strip()
    if monto_meta is not None:
        objetivo.monto_meta = reglas.normalizar_monto(monto_meta)
    if fecha_meta is not None:
        objetivo.fecha_meta = fecha_meta
    if archivado is not None:
        if archivado and almacen.saldos(usuario_id).apartado(objetivo_id) != 0:
            destino = "dólares" if objetivo.moneda is Moneda.USD else "ahorros"
            raise DatosInvalidos(f"Devolvé lo apartado a {destino} antes de archivar el objetivo")
        objetivo.archivado = archivado
    return almacen.guardar_objetivo(objetivo)


def eliminar_objetivo(almacen: Almacen, usuario_id: UUID, objetivo_id: UUID) -> None:
    if almacen.obtener_objetivo(usuario_id, objetivo_id) is None:
        raise NoEncontrado("El objetivo no existe")
    if almacen.objetivo_tiene_movimientos(usuario_id, objetivo_id):
        raise DatosInvalidos("El objetivo tiene movimientos; archivalo en lugar de borrarlo")
    almacen.eliminar_objetivo(usuario_id, objetivo_id)


# ---------------------------------------------------------------------------
# Resumen para el Inicio
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ResumenObjetivo:
    objetivo: Objetivo
    apartado: Decimal


@dataclass(frozen=True)
class Resumen:
    saldos: Saldos
    ingresos_periodo: Decimal
    gastos_periodo: Decimal
    objetivos: list[ResumenObjetivo]
    # Estimación de lo que se debe en tarjetas: no forma parte de "Tu plata"
    deuda_tarjetas: Decimal = Decimal(0)
    proximo_resumen_tarjetas: Decimal = Decimal(0)
    # Va aparte: ingresos y gastos del período son solo en pesos
    gastos_dolares_periodo: Decimal = Decimal(0)


def consultar_resumen(
    almacen: Almacen, usuario_id: UUID, desde: datetime, hasta: datetime, hoy: date
) -> Resumen:
    if desde >= hasta:
        raise DatosInvalidos("El período no es válido")
    saldos = almacen.saldos(usuario_id)
    ingresos, gastos = almacen.totales_periodo(usuario_id, desde, hasta)
    objetivos = [
        ResumenObjetivo(objetivo, saldos.apartado(objetivo.id))
        for objetivo in almacen.listar_objetivos(usuario_id)
        if not objetivo.archivado
    ]
    tarjetas = [
        calcular_estado(
            t, almacen.cuotas_por_mes(usuario_id, t.id), almacen.pagado_tarjeta(usuario_id, t.id), hoy
        )
        for t in almacen.listar_tarjetas(usuario_id)
    ]
    return Resumen(
        saldos,
        ingresos,
        gastos,
        objetivos,
        sum((t.deuda_estimada for t in tarjetas), Decimal(0)),
        sum((t.proximo_resumen for t in tarjetas), Decimal(0)),
        almacen.gastos_en_dolares(usuario_id, desde, hasta),
    )


def ubicacion(bolsillo: Bolsillo, objetivo_id: UUID | None = None) -> Ubicacion:
    """Construye una ubicación validando la combinación bolsillo/objetivo."""
    try:
        return Ubicacion(bolsillo, objetivo_id)
    except ValueError as error:
        raise DatosInvalidos(str(error)) from error
