"""Almacén en memoria para probar los casos de uso sin base de datos."""

from dataclasses import replace
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from app.dominio.modelos import Moneda, Movimiento, Objetivo, Saldos, TipoMovimiento
from app.dominio.puertos import Categoria, FiltroMovimientos, MetodoPago, Perfil
from app.dominio.tarjetas import CompraTarjeta, Tarjeta


class AlmacenEnMemoria:
    def __init__(self) -> None:
        self.movimientos: dict[UUID, Movimiento] = {}
        self.objetivos: dict[UUID, Objetivo] = {}
        self.categorias: dict[UUID, tuple[UUID, Categoria]] = {}
        self.metodos: dict[UUID, tuple[UUID, MetodoPago]] = {}
        self.bloqueos: list[UUID] = []
        self.perfiles: dict[UUID, Perfil] = {}
        self.tarjetas: dict[UUID, Tarjeta] = {}
        self.compras: dict[UUID, CompraTarjeta] = {}

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
        for m in self._del_periodo(usuario_id, desde, hasta, Moneda.ARS):
            if m.tipo is TipoMovimiento.INGRESO:
                ingresos += m.monto
            elif m.tipo is TipoMovimiento.GASTO:
                gastos += m.monto
        return ingresos, gastos

    def gastos_en_dolares(self, usuario_id: UUID, desde: datetime, hasta: datetime) -> Decimal:
        return sum(
            (
                m.monto
                for m in self._del_periodo(usuario_id, desde, hasta, Moneda.USD)
                if m.tipo is TipoMovimiento.GASTO
            ),
            Decimal(0),
        )

    def _del_periodo(
        self, usuario_id: UUID, desde: datetime, hasta: datetime, moneda: Moneda
    ) -> list[Movimiento]:
        return [
            m
            for m in self.movimientos.values()
            if m.usuario_id == usuario_id and desde <= m.ocurrido_en < hasta and m.moneda is moneda
        ]

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

    def obtener_perfil(self, usuario_id: UUID) -> Perfil | None:
        return self.perfiles.get(usuario_id)

    def actualizar_perfil(self, usuario_id: UUID, nombre_visible: str) -> Perfil:
        perfil = Perfil(usuario_id, nombre_visible, "ARS")
        self.perfiles[usuario_id] = perfil
        return perfil

    def listar_categorias(self, usuario_id: UUID) -> list[Categoria]:
        return [c for dueno, c in self.categorias.values() if dueno == usuario_id]

    def crear_categoria(
        self, usuario_id: UUID, nombre: str, tipo: TipoMovimiento, icono: str | None
    ) -> Categoria:
        categoria = Categoria(uuid4(), nombre, tipo, icono)
        self.categorias[categoria.id] = (usuario_id, categoria)
        return categoria

    def eliminar_categoria(self, usuario_id: UUID, categoria_id: UUID) -> None:
        if self.obtener_categoria(usuario_id, categoria_id):
            del self.categorias[categoria_id]

    def listar_metodos_pago(self, usuario_id: UUID) -> list[MetodoPago]:
        return [m for dueno, m in self.metodos.values() if dueno == usuario_id]

    def crear_metodo_pago(self, usuario_id: UUID, nombre: str, tipo: str) -> MetodoPago:
        metodo = MetodoPago(uuid4(), nombre, tipo, True)
        self.metodos[metodo.id] = (usuario_id, metodo)
        return metodo

    def actualizar_metodo_pago(self, usuario_id: UUID, metodo_pago_id: UUID, activo: bool) -> MetodoPago:
        _, metodo = self.metodos[metodo_pago_id]
        metodo = replace(metodo, activo=activo)
        self.metodos[metodo_pago_id] = (usuario_id, metodo)
        return metodo

    def objetivo_tiene_movimientos(self, usuario_id: UUID, objetivo_id: UUID) -> bool:
        return any(
            parte.ubicacion.objetivo_id == objetivo_id
            for m in self.movimientos.values()
            if m.usuario_id == usuario_id
            for parte in m.partes
        )

    # Tarjetas de crédito
    def guardar_tarjeta(self, tarjeta: Tarjeta) -> Tarjeta:
        tarjeta.id = tarjeta.id or uuid4()
        self.tarjetas[tarjeta.id] = tarjeta
        return tarjeta

    def obtener_tarjeta(self, usuario_id: UUID, tarjeta_id: UUID) -> Tarjeta | None:
        tarjeta = self.tarjetas.get(tarjeta_id)
        return tarjeta if tarjeta and tarjeta.usuario_id == usuario_id else None

    def listar_tarjetas(self, usuario_id: UUID) -> list[Tarjeta]:
        return [t for t in self.tarjetas.values() if t.usuario_id == usuario_id]

    def guardar_compra_tarjeta(self, compra: CompraTarjeta) -> CompraTarjeta:
        compra.id = compra.id or uuid4()
        self.compras[compra.id] = compra
        return compra

    def obtener_compra_tarjeta(self, usuario_id: UUID, compra_id: UUID) -> CompraTarjeta | None:
        compra = self.compras.get(compra_id)
        return compra if compra and compra.usuario_id == usuario_id else None

    def listar_compras_tarjeta(self, usuario_id: UUID, tarjeta_id: UUID) -> list[CompraTarjeta]:
        return [c for c in self.compras.values() if c.usuario_id == usuario_id and c.tarjeta_id == tarjeta_id]

    def eliminar_compra_tarjeta(self, usuario_id: UUID, compra_id: UUID) -> None:
        if self.obtener_compra_tarjeta(usuario_id, compra_id):
            del self.compras[compra_id]

    def cuotas_por_mes(self, usuario_id: UUID, tarjeta_id: UUID) -> dict[date, Decimal]:
        meses: dict[date, Decimal] = {}
        for compra in self.listar_compras_tarjeta(usuario_id, tarjeta_id):
            for cuota in compra.cuotas:
                meses[cuota.mes_resumen] = meses.get(cuota.mes_resumen, Decimal(0)) + cuota.monto
        return meses

    def pagado_tarjeta(self, usuario_id: UUID, tarjeta_id: UUID) -> Decimal:
        return sum(
            (
                m.monto
                for m in self.movimientos.values()
                if m.usuario_id == usuario_id and m.tarjeta_id == tarjeta_id
            ),
            Decimal(0),
        )
