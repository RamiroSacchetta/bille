"""Almacén en memoria para probar los casos de uso sin base de datos."""

from dataclasses import replace
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from app.dominio.modelos import Movimiento, Objetivo, Saldos, TipoMovimiento
from app.dominio.puertos import Categoria, FiltroMovimientos, MetodoPago


class AlmacenEnMemoria:
    def __init__(self) -> None:
        self.movimientos: dict[UUID, Movimiento] = {}
        self.objetivos: dict[UUID, Objetivo] = {}
        self.categorias: dict[UUID, tuple[UUID, Categoria]] = {}
        self.metodos: dict[UUID, tuple[UUID, MetodoPago]] = {}
        self.bloqueos: list[UUID] = []

    # Ayudas para preparar datos
    def agregar_categoria(self, usuario_id: UUID, nombre: str, tipo: TipoMovimiento) -> UUID:
        categoria = Categoria(uuid4(), nombre, tipo, None)
        self.categorias[categoria.id] = (usuario_id, categoria)
        return categoria.id

    def agregar_metodo(self, usuario_id: UUID, nombre: str) -> UUID:
        metodo = MetodoPago(uuid4(), nombre, "efectivo", True)
        self.metodos[metodo.id] = (usuario_id, metodo)
        return metodo.id

    # Implementación del puerto Almacen
    def bloquear_usuario(self, usuario_id: UUID) -> None:
        self.bloqueos.append(usuario_id)

    def saldos(self, usuario_id: UUID) -> Saldos:
        saldos = Saldos(Decimal(0), Decimal(0), {})
        for movimiento in self.movimientos.values():
            if movimiento.usuario_id == usuario_id:
                saldos = saldos.aplicar(movimiento.partes)
        return saldos

    def totales_periodo(self, usuario_id: UUID, desde: datetime, hasta: datetime) -> tuple[Decimal, Decimal]:
        ingresos = gastos = Decimal(0)
        for m in self.movimientos.values():
            if m.usuario_id == usuario_id and desde <= m.ocurrido_en < hasta:
                if m.tipo is TipoMovimiento.INGRESO:
                    ingresos += m.monto
                elif m.tipo is TipoMovimiento.GASTO:
                    gastos += m.monto
        return ingresos, gastos

    def guardar_movimiento(self, movimiento: Movimiento) -> Movimiento:
        guardado = replace(movimiento, id=movimiento.id or uuid4())
        self.movimientos[guardado.id] = guardado
        return guardado

    def obtener_movimiento(self, usuario_id: UUID, movimiento_id: UUID) -> Movimiento | None:
        movimiento = self.movimientos.get(movimiento_id)
        return movimiento if movimiento and movimiento.usuario_id == usuario_id else None

    def eliminar_movimiento(self, usuario_id: UUID, movimiento_id: UUID) -> None:
        if self.obtener_movimiento(usuario_id, movimiento_id):
            del self.movimientos[movimiento_id]

    def listar_movimientos(self, usuario_id: UUID, filtro: FiltroMovimientos) -> list[Movimiento]:
        return [m for m in self.movimientos.values() if m.usuario_id == usuario_id][: filtro.limite]

    def obtener_categoria(self, usuario_id: UUID, categoria_id: UUID) -> Categoria | None:
        dueno, categoria = self.categorias.get(categoria_id, (None, None))
        return categoria if dueno == usuario_id else None

    def obtener_metodo_pago(self, usuario_id: UUID, metodo_pago_id: UUID) -> MetodoPago | None:
        dueno, metodo = self.metodos.get(metodo_pago_id, (None, None))
        return metodo if dueno == usuario_id else None

    def guardar_objetivo(self, objetivo: Objetivo) -> Objetivo:
        objetivo.id = objetivo.id or uuid4()
        self.objetivos[objetivo.id] = objetivo
        return objetivo

    def obtener_objetivo(self, usuario_id: UUID, objetivo_id: UUID) -> Objetivo | None:
        objetivo = self.objetivos.get(objetivo_id)
        return objetivo if objetivo and objetivo.usuario_id == usuario_id else None

    def listar_objetivos(self, usuario_id: UUID) -> list[Objetivo]:
        return [o for o in self.objetivos.values() if o.usuario_id == usuario_id]

    def eliminar_objetivo(self, usuario_id: UUID, objetivo_id: UUID) -> None:
        if self.obtener_objetivo(usuario_id, objetivo_id):
            del self.objetivos[objetivo_id]

    def objetivo_tiene_movimientos(self, usuario_id: UUID, objetivo_id: UUID) -> bool:
        return any(
            parte.ubicacion.objetivo_id == objetivo_id
            for m in self.movimientos.values()
            if m.usuario_id == usuario_id
            for parte in m.partes
        )
