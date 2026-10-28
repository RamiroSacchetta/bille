"""Entidades del dominio de Bille.

La plata del usuario es una sola, repartida en dos bolsillos: disponible (la plata del mes) y ahorros.
Los objetivos son apartados dentro de ahorros. Cada movimiento tiene un total y una o más partes
que dicen de qué bolsillo (y objetivo) sale o entra la plata.
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


class Bolsillo(StrEnum):
    DISPONIBLE = "disponible"
    AHORROS = "ahorros"


@dataclass(frozen=True)
class Ubicacion:
    """Lugar donde está la plata: un bolsillo y, si es ahorros, opcionalmente un objetivo."""

    bolsillo: Bolsillo
    objetivo_id: UUID | None = None

    def __post_init__(self) -> None:
        if self.objetivo_id is not None and self.bolsillo is not Bolsillo.AHORROS:
            raise ValueError("Un objetivo solo puede estar dentro de ahorros")


DISPONIBLE = Ubicacion(Bolsillo.DISPONIBLE)
AHORRO_LIBRE = Ubicacion(Bolsillo.AHORROS)


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
    id: UUID | None = None


@dataclass
class Objetivo:
    usuario_id: UUID
    nombre: str
    monto_meta: Decimal
    fecha_meta: date | None = None
    archivado: bool = False
    id: UUID | None = None


@dataclass(frozen=True)
class Saldos:
    """Saldos actuales de un usuario, calculados a partir de las partes de sus movimientos."""

    disponible: Decimal
    ahorros: Decimal
    apartados: dict[UUID, Decimal] = field(default_factory=dict)

    @property
    def ahorro_libre(self) -> Decimal:
        return self.ahorros - sum(self.apartados.values(), Decimal(0))

    @property
    def total(self) -> Decimal:
        return self.disponible + self.ahorros

    def en(self, ubicacion: Ubicacion) -> Decimal:
        if ubicacion.bolsillo is Bolsillo.DISPONIBLE:
            return self.disponible
        if ubicacion.objetivo_id is None:
            return self.ahorro_libre
        return self.apartados.get(ubicacion.objetivo_id, Decimal(0))

    def aplicar(self, partes: list[Parte]) -> "Saldos":
        """Devuelve los saldos que quedarían después de aplicar (o revertir, con signo invertido) las partes."""
        disponible, ahorros, apartados = self.disponible, self.ahorros, dict(self.apartados)
        for parte in partes:
            if parte.ubicacion.bolsillo is Bolsillo.DISPONIBLE:
                disponible += parte.monto
            else:
                ahorros += parte.monto
                if parte.ubicacion.objetivo_id is not None:
                    objetivo = parte.ubicacion.objetivo_id
                    apartados[objetivo] = apartados.get(objetivo, Decimal(0)) + parte.monto
        return Saldos(disponible, ahorros, apartados)
