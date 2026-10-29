"""Entidades del dominio de Bille.

La plata del usuario es una sola, repartida en dos bolsillos: disponible (la plata del mes) y ahorros.
Los objetivos son apartados dentro de ahorros. Cada movimiento tiene un total y una o más partes
que dicen de qué bolsillo (y objetivo) sale o entra la plata.

Los dólares son un bolsillo aparte, con sus propios objetivos, que nunca se convierte ni se suma a los pesos.
Cada parte está en la moneda de su bolsillo; el cambio es el único movimiento que mezcla las dos monedas.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID


class TipoMovimiento(StrEnum):
    INGRESO = "ingreso"
    GASTO = "gasto"
    TRANSFERENCIA = "transferencia"
    CAMBIO = "cambio"


class Moneda(StrEnum):
    ARS = "ARS"
    USD = "USD"


class OperacionCambio(StrEnum):
    COMPRA = "compra"
    VENTA = "venta"


class Bolsillo(StrEnum):
    DISPONIBLE = "disponible"
    AHORROS = "ahorros"
    DOLARES = "dolares"

    @property
    def moneda(self) -> Moneda:
        return Moneda.USD if self is Bolsillo.DOLARES else Moneda.ARS


@dataclass(frozen=True)
class Ubicacion:
    """Lugar donde está la plata: un bolsillo y, si es ahorros o dólares, opcionalmente un objetivo."""

    bolsillo: Bolsillo
    objetivo_id: UUID | None = None

    def __post_init__(self) -> None:
        if self.objetivo_id is not None and self.bolsillo is Bolsillo.DISPONIBLE:
            raise ValueError("Un objetivo solo puede estar dentro de ahorros")

    @property
    def moneda(self) -> Moneda:
        return self.bolsillo.moneda


DISPONIBLE = Ubicacion(Bolsillo.DISPONIBLE)
AHORRO_LIBRE = Ubicacion(Bolsillo.AHORROS)
DOLARES_LIBRES = Ubicacion(Bolsillo.DOLARES)


@dataclass(frozen=True)
class Parte:
    """Monto con signo: positivo entra a la ubicación, negativo sale."""

    ubicacion: Ubicacion
    monto: Decimal


@dataclass
class Movimiento:
    usuario_id: UUID
    tipo: TipoMovimiento
    monto: Decimal
    ocurrido_en: datetime
    partes: list[Parte]
    descripcion: str | None = None
    categoria_id: UUID | None = None
    metodo_pago_id: UUID | None = None
    # Solo en gastos: la tarjeta de crédito cuyo resumen se pagó
    tarjeta_id: UUID | None = None
    # En un cambio el monto son los dólares, así que la moneda es USD
    moneda: Moneda = Moneda.ARS
    # Lo genera el dispositivo: si la misma carga llega dos veces, se guarda una sola
    id_carga: UUID | None = None
    id: UUID | None = None


@dataclass
class Objetivo:
    usuario_id: UUID
    nombre: str
    monto_meta: Decimal
    fecha_meta: date | None = None
    archivado: bool = False
    moneda: Moneda = Moneda.ARS
    id: UUID | None = None


@dataclass(frozen=True)
class Saldos:
    """Saldos actuales de un usuario, calculados a partir de las partes de sus movimientos.

    `apartados` son los objetivos en pesos (dentro de ahorros) y `apartados_dolares` los objetivos en dólares.
    """

    disponible: Decimal
    ahorros: Decimal
    apartados: dict[UUID, Decimal] = field(default_factory=dict)
    dolares: Decimal = Decimal(0)
    apartados_dolares: dict[UUID, Decimal] = field(default_factory=dict)

    @property
    def ahorro_libre(self) -> Decimal:
        return self.ahorros - sum(self.apartados.values(), Decimal(0))

    @property
    def dolares_libres(self) -> Decimal:
        return self.dolares - sum(self.apartados_dolares.values(), Decimal(0))

    @property
    def total(self) -> Decimal:
        """Solo pesos: los dólares nunca se suman."""
        return self.disponible + self.ahorros

    def apartado(self, objetivo_id: UUID) -> Decimal:
        return self.apartados.get(objetivo_id, self.apartados_dolares.get(objetivo_id, Decimal(0)))

    def en(self, ubicacion: Ubicacion) -> Decimal:
        if ubicacion.bolsillo is Bolsillo.DISPONIBLE:
            return self.disponible
        if ubicacion.objetivo_id is not None:
            return self.apartado(ubicacion.objetivo_id)
        return self.dolares_libres if ubicacion.bolsillo is Bolsillo.DOLARES else self.ahorro_libre

    def aplicar(self, partes: list[Parte]) -> "Saldos":
        """Devuelve los saldos que quedarían después de aplicar (o revertir, con signo invertido) las partes."""
        disponible, ahorros, dolares = self.disponible, self.ahorros, self.dolares
        apartados, apartados_dolares = dict(self.apartados), dict(self.apartados_dolares)
        for parte in partes:
            if parte.ubicacion.bolsillo is Bolsillo.DISPONIBLE:
                disponible += parte.monto
                continue
            if parte.ubicacion.bolsillo is Bolsillo.DOLARES:
                dolares += parte.monto
                destino = apartados_dolares
            else:
                ahorros += parte.monto
                destino = apartados
            if parte.ubicacion.objetivo_id is not None:
                objetivo = parte.ubicacion.objetivo_id
                destino[objetivo] = destino.get(objetivo, Decimal(0)) + parte.monto
        return Saldos(disponible, ahorros, apartados, dolares, apartados_dolares)
