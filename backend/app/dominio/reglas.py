"""Reglas de negocio puras: cómo se arman las partes de cada movimiento y cuándo son válidas."""

from decimal import Decimal

from app.dominio.errores import DatosInvalidos, SaldoInsuficiente
from app.dominio.modelos import Bolsillo, Parte, Saldos, TipoMovimiento, Ubicacion

CENTAVO = Decimal("0.01")


def normalizar_monto(monto: Decimal) -> Decimal:
    if monto <= 0:
        raise DatosInvalidos("El monto tiene que ser mayor a cero")
    if monto != monto.quantize(CENTAVO):
        raise DatosInvalidos("El monto admite como máximo dos decimales")
    return monto.quantize(CENTAVO)


def nombre_ubicacion(ubicacion: Ubicacion) -> str:
    if ubicacion.bolsillo is Bolsillo.DISPONIBLE:
        return "la plata del mes"
    if ubicacion.objetivo_id is None:
        return "el ahorro libre"
    return "el objetivo"


def partes_de_gasto(monto: Decimal, origenes: list[tuple[Ubicacion, Decimal]]) -> list[Parte]:
    """Un gasto sale de uno o más orígenes; los montos de los orígenes tienen que sumar el total."""
    if not origenes:
        raise DatosInvalidos("Indicá de dónde sale la plata del gasto")
    ubicaciones = [ubicacion for ubicacion, _ in origenes]
    if len(set(ubicaciones)) != len(ubicaciones):
        raise DatosInvalidos("Cada origen del pago puede aparecer una sola vez")
    montos = [normalizar_monto(parcial) for _, parcial in origenes]
    if sum(montos, Decimal(0)) != monto:
        raise DatosInvalidos("Las partes del pago tienen que sumar el total del gasto")
    return [Parte(ubicacion, -parcial) for ubicacion, parcial in zip(ubicaciones, montos, strict=True)]


def partes_de_ingreso(monto: Decimal, destino: Ubicacion) -> list[Parte]:
    return [Parte(destino, monto)]


def partes_de_transferencia(monto: Decimal, desde: Ubicacion, hacia: Ubicacion) -> list[Parte]:
    if desde == hacia:
        raise DatosInvalidos("El origen y el destino de la transferencia tienen que ser distintos")
    return [Parte(desde, -monto), Parte(hacia, monto)]


def validar_cuadre(tipo: TipoMovimiento, monto: Decimal, partes: list[Parte]) -> None:
    """Misma regla que el trigger de la base: protege antes de llegar a Postgres."""
    suma = sum((parte.monto for parte in partes), Decimal(0))
    if tipo is TipoMovimiento.INGRESO and (suma != monto or any(p.monto < 0 for p in partes)):
        raise DatosInvalidos("Las partes del ingreso tienen que ser positivas y sumar el total")
    if tipo is TipoMovimiento.GASTO and (suma != -monto or any(p.monto > 0 for p in partes)):
        raise DatosInvalidos("Las partes del gasto tienen que ser negativas y sumar el total")
    if tipo is TipoMovimiento.TRANSFERENCIA and (len(partes) < 2 or suma != 0):
        raise DatosInvalidos("Las partes de la transferencia tienen que sumar cero")


def validar_saldos(saldos: Saldos) -> None:
    """Ningún bolsillo, ni el ahorro libre, ni un objetivo pueden quedar en negativo."""
    if saldos.disponible < 0:
        raise SaldoInsuficiente("No te alcanza la plata del mes para este movimiento")
    if saldos.ahorro_libre < 0:
        raise SaldoInsuficiente("No te alcanza el ahorro libre para este movimiento")
    if any(apartado < 0 for apartado in saldos.apartados.values()):
        raise SaldoInsuficiente("No te alcanza lo apartado en el objetivo para este movimiento")
