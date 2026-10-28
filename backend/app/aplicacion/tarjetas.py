"""Casos de uso de tarjetas de crédito: alta, compras en cuotas, estado y pago del resumen."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from app.aplicacion import casos_uso as cu
from app.dominio import reglas
from app.dominio.errores import DatosInvalidos, NoEncontrado
from app.dominio.modelos import Movimiento, TipoMovimiento, Ubicacion
from app.dominio.puertos import Almacen
from app.dominio.tarjetas import (
    CompraTarjeta,
    EstadoTarjeta,
    Tarjeta,
    calcular_estado,
    dividir_en_cuotas,
    mes_de_resumen,
    validar_dia,
)


def _nombre(nombre: str) -> str:
    nombre = nombre.strip()
    if not nombre:
        raise DatosInvalidos("La tarjeta necesita un nombre")
    if len(nombre) > 60:
        raise DatosInvalidos("El nombre de la tarjeta admite hasta 60 caracteres")
    return nombre


def _tarjeta(almacen: Almacen, usuario_id: UUID, tarjeta_id: UUID) -> Tarjeta:
    tarjeta = almacen.obtener_tarjeta(usuario_id, tarjeta_id)
    if tarjeta is None:
        raise NoEncontrado("La tarjeta no existe")
    return tarjeta


def crear_tarjeta(
    almacen: Almacen, usuario_id: UUID, nombre: str, dia_cierre: int, dia_vencimiento: int
) -> Tarjeta:
    tarjeta = Tarjeta(
        usuario_id,
        _nombre(nombre),
        validar_dia(dia_cierre, "cierre"),
        validar_dia(dia_vencimiento, "vencimiento"),
    )
    return almacen.guardar_tarjeta(tarjeta)


def actualizar_tarjeta(
    almacen: Almacen,
    usuario_id: UUID,
    tarjeta_id: UUID,
    nombre: str | None = None,
    dia_cierre: int | None = None,
    dia_vencimiento: int | None = None,
    activa: bool | None = None,
) -> Tarjeta:
    tarjeta = _tarjeta(almacen, usuario_id, tarjeta_id)
    if nombre is not None:
        tarjeta.nombre = _nombre(nombre)
    if dia_cierre is not None:
        tarjeta.dia_cierre = validar_dia(dia_cierre, "cierre")
    if dia_vencimiento is not None:
        tarjeta.dia_vencimiento = validar_dia(dia_vencimiento, "vencimiento")
    if activa is not None:
        tarjeta.activa = activa
    return almacen.guardar_tarjeta(tarjeta)


def registrar_compra(
    almacen: Almacen,
    usuario_id: UUID,
    tarjeta_id: UUID,
    monto: Decimal,
    cantidad_cuotas: int,
    comprado_en: date,
    categoria_id: UUID | None = None,
    descripcion: str | None = None,
) -> CompraTarjeta:
    """Anota una compra con tarjeta. No mueve plata: suma cuotas a la deuda estimada de la tarjeta."""
    monto = reglas.normalizar_monto(monto)
    tarjeta = _tarjeta(almacen, usuario_id, tarjeta_id)
    if not tarjeta.activa:
        raise DatosInvalidos("La tarjeta está desactivada")
    if categoria_id is not None:
        categoria = almacen.obtener_categoria(usuario_id, categoria_id)
        if categoria is None:
            raise NoEncontrado("La categoría no existe")
        if categoria.tipo is not TipoMovimiento.GASTO:
            raise DatosInvalidos("La categoría elegida no es de gasto")
    cuotas = dividir_en_cuotas(monto, cantidad_cuotas, mes_de_resumen(comprado_en, tarjeta.dia_cierre))
    compra = CompraTarjeta(
        usuario_id=usuario_id,
        tarjeta_id=tarjeta_id,
        monto_total=monto,
        cantidad_cuotas=cantidad_cuotas,
        comprado_en=comprado_en,
        cuotas=cuotas,
        descripcion=descripcion,
        categoria_id=categoria_id,
    )
    return almacen.guardar_compra_tarjeta(compra)


def eliminar_compra(almacen: Almacen, usuario_id: UUID, compra_id: UUID) -> None:
    if almacen.obtener_compra_tarjeta(usuario_id, compra_id) is None:
        raise NoEncontrado("La compra no existe")
    almacen.eliminar_compra_tarjeta(usuario_id, compra_id)


def pagar_resumen(
    almacen: Almacen,
    usuario_id: UUID,
    tarjeta_id: UUID,
    monto: Decimal,
    ocurrido_en: datetime,
    origenes: list[tuple[Ubicacion, Decimal]] | None = None,
) -> Movimiento:
    """El pago real del resumen: es el gasto del mes, sale de tu plata y baja la deuda de la tarjeta.

    Puede ser distinto de lo estimado: si pagás menos, el resto queda pendiente.
    """
    tarjeta = _tarjeta(almacen, usuario_id, tarjeta_id)
    return cu.registrar_gasto(
        almacen,
        usuario_id,
        monto,
        ocurrido_en,
        descripcion=f"Pago de tarjeta {tarjeta.nombre}",
        origenes=origenes,
        tarjeta_id=tarjeta.id,
    )


def estado_tarjetas(almacen: Almacen, usuario_id: UUID, hoy: date) -> list[EstadoTarjeta]:
    return [
        calcular_estado(
            tarjeta,
            almacen.cuotas_por_mes(usuario_id, tarjeta.id),
            almacen.pagado_tarjeta(usuario_id, tarjeta.id),
            hoy,
        )
        for tarjeta in almacen.listar_tarjetas(usuario_id)
    ]
