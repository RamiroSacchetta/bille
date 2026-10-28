"""Puertos: lo que el dominio necesita del mundo exterior, sin saber cómo se implementa."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from app.dominio.modelos import Movimiento, Objetivo, Saldos, TipoMovimiento


@dataclass(frozen=True)
class Categoria:
    id: UUID
    nombre: str
    tipo: TipoMovimiento
    icono: str | None


@dataclass(frozen=True)
class MetodoPago:
    id: UUID
    nombre: str
    tipo: str
    activo: bool


@dataclass(frozen=True)
class Perfil:
    id: UUID
    nombre_visible: str
    moneda_predeterminada: str


@dataclass(frozen=True)
class FiltroMovimientos:
    desde: datetime | None = None
    hasta: datetime | None = None
    tipo: TipoMovimiento | None = None
    categoria_id: UUID | None = None
    limite: int = 200


class Almacen(Protocol):
    """Acceso a los datos de UN usuario dentro de una transacción."""

    def bloquear_usuario(self, usuario_id: UUID) -> None:
        """Serializa las escrituras del usuario para que dos cargas simultáneas no dejen saldos negativos."""

    def saldos(self, usuario_id: UUID) -> Saldos: ...

    def totales_periodo(self, usuario_id: UUID, desde: datetime, hasta: datetime) -> tuple[Decimal, Decimal]:
        """Devuelve (ingresos, gastos) del período; las transferencias no cuentan."""

    def guardar_movimiento(self, movimiento: Movimiento) -> Movimiento: ...

    def obtener_movimiento(self, usuario_id: UUID, movimiento_id: UUID) -> Movimiento | None: ...

    def eliminar_movimiento(self, usuario_id: UUID, movimiento_id: UUID) -> None: ...

    def listar_movimientos(self, usuario_id: UUID, filtro: FiltroMovimientos) -> list[Movimiento]: ...

    def obtener_categoria(self, usuario_id: UUID, categoria_id: UUID) -> Categoria | None: ...

    def obtener_metodo_pago(self, usuario_id: UUID, metodo_pago_id: UUID) -> MetodoPago | None: ...

    def guardar_objetivo(self, objetivo: Objetivo) -> Objetivo: ...

    def obtener_objetivo(self, usuario_id: UUID, objetivo_id: UUID) -> Objetivo | None: ...

    def listar_objetivos(self, usuario_id: UUID) -> list[Objetivo]: ...

    def eliminar_objetivo(self, usuario_id: UUID, objetivo_id: UUID) -> None: ...

    def objetivo_tiene_movimientos(self, usuario_id: UUID, objetivo_id: UUID) -> bool: ...

    # Catálogo del usuario: perfil, categorías y métodos de pago

    def obtener_perfil(self, usuario_id: UUID) -> Perfil | None: ...

    def actualizar_perfil(self, usuario_id: UUID, nombre_visible: str) -> Perfil: ...

    def listar_categorias(self, usuario_id: UUID) -> list[Categoria]: ...

    def crear_categoria(
        self, usuario_id: UUID, nombre: str, tipo: TipoMovimiento, icono: str | None
    ) -> Categoria: ...

    def eliminar_categoria(self, usuario_id: UUID, categoria_id: UUID) -> None: ...

    def listar_metodos_pago(self, usuario_id: UUID) -> list[MetodoPago]: ...

    def crear_metodo_pago(self, usuario_id: UUID, nombre: str, tipo: str) -> MetodoPago: ...

    def actualizar_metodo_pago(self, usuario_id: UUID, metodo_pago_id: UUID, activo: bool) -> MetodoPago: ...
