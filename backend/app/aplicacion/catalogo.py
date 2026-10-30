"""Casos de uso del catálogo: perfil, categorías y métodos de pago."""

from uuid import UUID

from app.dominio.errores import DatosInvalidos, NoEncontrado
from app.dominio.modelos import MonedaPrincipal, TipoMovimiento
from app.dominio.puertos import Almacen, Categoria, MetodoPago, Perfil

TIPOS_METODO_PAGO = {"efectivo", "billetera", "debito", "credito", "banco"}


def _texto(valor: str, campo: str, maximo: int) -> str:
    valor = valor.strip()
    if not valor:
        raise DatosInvalidos(f"Completá el {campo}")
    if len(valor) > maximo:
        raise DatosInvalidos(f"El {campo} admite hasta {maximo} caracteres")
    return valor


def obtener_perfil(almacen: Almacen, usuario_id: UUID) -> Perfil:
    perfil = almacen.obtener_perfil(usuario_id)
    if perfil is None:
        raise NoEncontrado("El perfil no existe")
    return perfil


def actualizar_perfil(
    almacen: Almacen,
    usuario_id: UUID,
    nombre_visible: str | None = None,
    moneda_predeterminada: MonedaPrincipal | None = None,
) -> Perfil:
    """Solo cambia lo que se manda. La moneda no convierte montos: cambia cómo se muestran."""
    nombre = _texto(nombre_visible, "nombre", 80) if nombre_visible is not None else None
    moneda = moneda_predeterminada.value if moneda_predeterminada is not None else None
    return almacen.actualizar_perfil(usuario_id, nombre, moneda)


def crear_categoria(
    almacen: Almacen, usuario_id: UUID, nombre: str, tipo: TipoMovimiento, icono: str | None = None
) -> Categoria:
    if tipo is TipoMovimiento.TRANSFERENCIA:
        raise DatosInvalidos("Las categorías son solo de ingreso o de gasto")
    return almacen.crear_categoria(usuario_id, _texto(nombre, "nombre", 60), tipo, icono)


def eliminar_categoria(almacen: Almacen, usuario_id: UUID, categoria_id: UUID) -> None:
    if almacen.obtener_categoria(usuario_id, categoria_id) is None:
        raise NoEncontrado("La categoría no existe")
    almacen.eliminar_categoria(usuario_id, categoria_id)


def crear_metodo_pago(almacen: Almacen, usuario_id: UUID, nombre: str, tipo: str) -> MetodoPago:
    if tipo not in TIPOS_METODO_PAGO:
        raise DatosInvalidos("El tipo de método de pago no es válido")
    return almacen.crear_metodo_pago(usuario_id, _texto(nombre, "nombre", 60), tipo)


def actualizar_metodo_pago(
    almacen: Almacen, usuario_id: UUID, metodo_pago_id: UUID, activo: bool
) -> MetodoPago:
    if almacen.obtener_metodo_pago(usuario_id, metodo_pago_id) is None:
        raise NoEncontrado("El método de pago no existe")
    return almacen.actualizar_metodo_pago(usuario_id, metodo_pago_id, activo)
