"""Esquemas de entrada y salida de la API. Los montos viajan como texto para no perder precisión."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.aplicacion.casos_uso import Resumen
from app.dominio.modelos import Bolsillo, Movimiento, Objetivo, TipoMovimiento

Monto = Decimal


class UbicacionEntrada(BaseModel):
    bolsillo: Bolsillo
    objetivo_id: UUID | None = None


class OrigenEntrada(UbicacionEntrada):
    monto: Monto


class IngresoEntrada(BaseModel):
    monto: Monto
    ocurrido_en: datetime
    categoria_id: UUID | None = None
    metodo_pago_id: UUID | None = None
    descripcion: str | None = Field(default=None, max_length=200)
    destino: UbicacionEntrada = UbicacionEntrada(bolsillo=Bolsillo.DISPONIBLE)


class GastoEntrada(BaseModel):
    monto: Monto
    ocurrido_en: datetime
    categoria_id: UUID | None = None
    metodo_pago_id: UUID | None = None
    descripcion: str | None = Field(default=None, max_length=200)
    # Sin orígenes, el gasto sale entero de la plata del mes
    origenes: list[OrigenEntrada] | None = Field(default=None, max_length=10)


class TransferenciaEntrada(BaseModel):
    monto: Monto
    ocurrido_en: datetime
    desde: UbicacionEntrada
    hacia: UbicacionEntrada
    descripcion: str | None = Field(default=None, max_length=200)


class ParteSalida(BaseModel):
    bolsillo: Bolsillo
    objetivo_id: UUID | None
    monto: Monto


class MovimientoSalida(BaseModel):
    id: UUID
    tipo: TipoMovimiento
    monto: Monto
    ocurrido_en: datetime
    descripcion: str | None
    categoria_id: UUID | None
    metodo_pago_id: UUID | None
    partes: list[ParteSalida]

    @classmethod
    def desde(cls, m: Movimiento) -> "MovimientoSalida":
        return cls(
            id=m.id,
            tipo=m.tipo,
            monto=m.monto,
            ocurrido_en=m.ocurrido_en,
            descripcion=m.descripcion,
            categoria_id=m.categoria_id,
            metodo_pago_id=m.metodo_pago_id,
            partes=[
                ParteSalida(bolsillo=p.ubicacion.bolsillo, objetivo_id=p.ubicacion.objetivo_id, monto=p.monto)
                for p in m.partes
            ],
        )


class ObjetivoEntrada(BaseModel):
    nombre: str = Field(max_length=80)
    monto_meta: Monto
    fecha_meta: date | None = None


class ObjetivoCambios(BaseModel):
    nombre: str | None = Field(default=None, max_length=80)
    monto_meta: Monto | None = None
    fecha_meta: date | None = None
    archivado: bool | None = None


class ObjetivoSalida(BaseModel):
    id: UUID
    nombre: str
    monto_meta: Monto
    fecha_meta: date | None
    archivado: bool
    apartado: Monto

    @classmethod
    def desde(cls, o: Objetivo, apartado: Decimal) -> "ObjetivoSalida":
        return cls(
            id=o.id,
            nombre=o.nombre,
            monto_meta=o.monto_meta,
            fecha_meta=o.fecha_meta,
            archivado=o.archivado,
            apartado=apartado,
        )


class SaldosSalida(BaseModel):
    total: Monto
    disponible: Monto
    ahorros: Monto
    ahorro_libre: Monto


class ResumenSalida(BaseModel):
    saldos: SaldosSalida
    ingresos_mes: Monto
    gastos_mes: Monto
    objetivos: list[ObjetivoSalida]

    @classmethod
    def desde(cls, r: Resumen) -> "ResumenSalida":
        s = r.saldos
        return cls(
            saldos=SaldosSalida(
                total=s.total, disponible=s.disponible, ahorros=s.ahorros, ahorro_libre=s.ahorro_libre
            ),
            ingresos_mes=r.ingresos_periodo,
            gastos_mes=r.gastos_periodo,
            objetivos=[ObjetivoSalida.desde(o.objetivo, o.apartado) for o in r.objetivos],
        )


class PerfilSalida(BaseModel):
    id: UUID
    nombre_visible: str
    moneda_predeterminada: str


class PerfilCambios(BaseModel):
    nombre_visible: str = Field(max_length=80)


class CategoriaEntrada(BaseModel):
    nombre: str = Field(max_length=60)
    tipo: TipoMovimiento
    icono: str | None = Field(default=None, max_length=30)


class CategoriaSalida(BaseModel):
    id: UUID
    nombre: str
    tipo: TipoMovimiento
    icono: str | None


class MetodoPagoEntrada(BaseModel):
    nombre: str = Field(max_length=60)
    tipo: str


class MetodoPagoCambios(BaseModel):
    activo: bool


class MetodoPagoSalida(BaseModel):
    id: UUID
    nombre: str
    tipo: str
    activo: bool
