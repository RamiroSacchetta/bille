"""Reglas de negocio puras: cómo se arman las partes de cada movimiento y cuándo son válidas."""

from decimal import Decimal

from app.dominio.errores import DatosInvalidos, SaldoInsuficiente
from app.dominio.modelos import (
    DOLARES_LIBRES,
    Bolsillo,
    Moneda,
    OperacionCambio,
    Parte,
    Saldos,
    TipoMovimiento,
    Ubicacion,
)

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
    if ubicacion.objetivo_id is not None:
        return "el objetivo"
    return "los dólares libres" if ubicacion.bolsillo is Bolsillo.DOLARES else "el ahorro libre"


def moneda_de(partes: list[Parte]) -> Moneda:
    """Moneda de un movimiento que no es un cambio: la de sus partes (todas en la misma)."""
    return partes[0].ubicacion.moneda if partes else Moneda.ARS


def partes_de_gasto(monto: Decimal, origenes: list[tuple[Ubicacion, Decimal]]) -> list[Parte]:
    """Un gasto sale de uno o más orígenes de la misma moneda; los montos tienen que sumar el total."""
    if not origenes:
        raise DatosInvalidos("Indicá de dónde sale la plata del gasto")
    ubicaciones = [ubicacion for ubicacion, _ in origenes]
    if len(set(ubicaciones)) != len(ubicaciones):
        raise DatosInvalidos("Cada origen del pago puede aparecer una sola vez")
    if len({ubicacion.moneda for ubicacion in ubicaciones}) > 1:
        raise DatosInvalidos("Un gasto va en una sola moneda")
    montos = [normalizar_monto(parcial) for _, parcial in origenes]
    if sum(montos, Decimal(0)) != monto:
        raise DatosInvalidos("Las partes del pago tienen que sumar el total del gasto")
    return [Parte(ubicacion, -parcial) for ubicacion, parcial in zip(ubicaciones, montos, strict=True)]


def partes_de_ingreso(monto: Decimal, destino: Ubicacion) -> list[Parte]:
    return [Parte(destino, monto)]


def partes_de_transferencia(monto: Decimal, desde: Ubicacion, hacia: Ubicacion) -> list[Parte]:
    if desde == hacia:
        raise DatosInvalidos("El origen y el destino de la transferencia tienen que ser distintos")
    if desde.moneda is not hacia.moneda:
        raise DatosInvalidos("Para pasar entre pesos y dólares usá Comprar o Vender dólares")
    return [Parte(desde, -monto), Parte(hacia, monto)]


def partes_de_cambio(
    operacion: OperacionCambio, dolares: Decimal, pesos: Decimal, pesos_en: Ubicacion
) -> list[Parte]:
    """Comprar: salen pesos y entran dólares libres. Vender: salen dólares libres y entran pesos."""
    if pesos_en.moneda is not Moneda.ARS or pesos_en.objetivo_id is not None:
        raise DatosInvalidos("Los pesos del cambio van a la plata del mes o al ahorro libre en pesos")
    # Primero lo que sale y después lo que entra
    if operacion is OperacionCambio.COMPRA:
        return [Parte(pesos_en, -pesos), Parte(DOLARES_LIBRES, dolares)]
    return [Parte(DOLARES_LIBRES, -dolares), Parte(pesos_en, pesos)]


def validar_cuadre(tipo: TipoMovimiento, monto: Decimal, partes: list[Parte]) -> None:
    """Misma regla que el trigger de la base: protege antes de llegar a Postgres."""
    if tipo is TipoMovimiento.CAMBIO:
        en_dolares = [p for p in partes if p.ubicacion.moneda is Moneda.USD]
        en_pesos = [p for p in partes if p.ubicacion.moneda is Moneda.ARS]
        if (
            len(en_dolares) != 1
            or len(en_pesos) != 1
            or abs(en_dolares[0].monto) != monto
            or (en_dolares[0].monto > 0) == (en_pesos[0].monto > 0)
        ):
            raise DatosInvalidos(
                "El cambio necesita una parte en dólares y otra en pesos con signos opuestos"
            )
        return
    if len({p.ubicacion.moneda for p in partes}) > 1:
        raise DatosInvalidos("Las partes del movimiento tienen que estar en una sola moneda")
    suma = sum((parte.monto for parte in partes), Decimal(0))
    if tipo is TipoMovimiento.INGRESO and (suma != monto or any(p.monto < 0 for p in partes)):
        raise DatosInvalidos("Las partes del ingreso tienen que ser positivas y sumar el total")
    if tipo is TipoMovimiento.GASTO and (suma != -monto or any(p.monto > 0 for p in partes)):
        raise DatosInvalidos("Las partes del gasto tienen que ser negativas y sumar el total")
    if tipo is TipoMovimiento.TRANSFERENCIA and (len(partes) < 2 or suma != 0):
        raise DatosInvalidos("Las partes de la transferencia tienen que sumar cero")


def validar_saldos(saldos: Saldos) -> None:
    """Ningún bolsillo, ni lo libre, ni un objetivo pueden quedar en negativo, en ninguna moneda."""
    if saldos.disponible < 0:
        raise SaldoInsuficiente("No te alcanza la plata del mes para este movimiento")
    if saldos.ahorro_libre < 0:
        raise SaldoInsuficiente("No te alcanza el ahorro libre para este movimiento")
    if saldos.dolares_libres < 0:
        raise SaldoInsuficiente("No te alcanzan los dólares libres para este movimiento")
    if any(apartado < 0 for apartado in [*saldos.apartados.values(), *saldos.apartados_dolares.values()]):
        raise SaldoInsuficiente("No te alcanza lo apartado en el objetivo para este movimiento")
