"""Esquemas de entrada y salida de la API. Los montos viajan como texto para no perder precisión."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.aplicacion.casos_uso import Resumen
from app.dominio.modelos import Bolsillo, Moneda, Movimiento, Objetivo, OperacionCambio, TipoMovimiento
from app.dominio.tarjetas import CompraTarjeta, EstadoTarjeta

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
    # Lo genera el dispositivo: si la misma carga llega dos veces, se devuelve lo ya guardado
    id_carga: UUID | None = None


class GastoEntrada(BaseModel):
    monto: Monto
    ocurrido_en: datetime
    categoria_id: UUID | None = None
    metodo_pago_id: UUID | None = None
    descripcion: str | None = Field(default=None, max_length=200)
    # Sin orígenes, el gasto sale entero de la plata del mes
    origenes: list[OrigenEntrada] | None = Field(default=None, max_length=10)
    # Lo genera el dispositivo: si la misma carga llega dos veces, se devuelve lo ya guardado
    id_carga: UUID | None = None


class TransferenciaEntrada(BaseModel):
    monto: Monto
    ocurrido_en: datetime
    desde: UbicacionEntrada
    hacia: UbicacionEntrada
    descripcion: str | None = Field(default=None, max_length=200)


class PesosEntrada(BaseModel):
    """Dónde están los pesos de un cambio: la plata del mes o el ahorro libre."""

    bolsillo: Bolsillo = Bolsillo.DISPONIBLE


class CambioEntrada(BaseModel):
    operacion: OperacionCambio
    dolares: Monto
    pesos: Monto
    ocurrido_en: datetime
    # De dónde salen los pesos al comprar o adónde entran al vender
    pesos_en: PesosEntrada = PesosEntrada()
    descripcion: str | None = Field(default=None, max_length=200)
    # Lo genera el dispositivo: si la misma carga llega dos veces, se devuelve lo ya guardado
    id_carga: UUID | None = None


class ParteSalida(BaseModel):
    bolsillo: Bolsillo
    objetivo_id: UUID | None
    monto: Monto


class MovimientoSalida(BaseModel):
    id: UUID
    tipo: TipoMovimiento
    monto: Monto
    moneda: Moneda
    ocurrido_en: datetime
    descripcion: str | None
    categoria_id: UUID | None
    metodo_pago_id: UUID | None
    tarjeta_id: UUID | None = None
    partes: list[ParteSalida]

    @classmethod
    def desde(cls, m: Movimiento) -> "MovimientoSalida":
        return cls(
            id=m.id,
            tipo=m.tipo,
            monto=m.monto,
            moneda=m.moneda,
            ocurrido_en=m.ocurrido_en,
            descripcion=m.descripcion,
            categoria_id=m.categoria_id,
            metodo_pago_id=m.metodo_pago_id,
            tarjeta_id=m.tarjeta_id,
            partes=[
                ParteSalida(bolsillo=p.ubicacion.bolsillo, objetivo_id=p.ubicacion.objetivo_id, monto=p.monto)
                for p in m.partes
            ],
        )


class ObjetivoEntrada(BaseModel):
    nombre: str = Field(max_length=80)
    monto_meta: Monto
    fecha_meta: date | None = None
    moneda: Moneda = Moneda.ARS


class ObjetivoCambios(BaseModel):
    nombre: str | None = Field(default=None, max_length=80)
    monto_meta: Monto | None = None
    fecha_meta: date | None = None
    archivado: bool | None = None


class ObjetivoSalida(BaseModel):
    id: UUID
    nombre: str
    moneda: Moneda
    monto_meta: Monto
    fecha_meta: date | None
    archivado: bool
    apartado: Monto

    @classmethod
    def desde(cls, o: Objetivo, apartado: Decimal) -> "ObjetivoSalida":
        return cls(
            id=o.id,
            nombre=o.nombre,
            moneda=o.moneda,
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
    dolares: Monto
    dolares_libres: Monto


class ResumenSalida(BaseModel):
    saldos: SaldosSalida
    ingresos_mes: Monto
    gastos_mes: Monto
    gastos_dolares_mes: Monto
    objetivos: list[ObjetivoSalida]
    deuda_tarjetas: Monto
    proximo_resumen_tarjetas: Monto

    @classmethod
    def desde(cls, r: Resumen) -> "ResumenSalida":
        s = r.saldos
        return cls(
            saldos=SaldosSalida(
                total=s.total,
                disponible=s.disponible,
                ahorros=s.ahorros,
                ahorro_libre=s.ahorro_libre,
                dolares=s.dolares,
                dolares_libres=s.dolares_libres,
            ),
            ingresos_mes=r.ingresos_periodo,
            gastos_mes=r.gastos_periodo,
            gastos_dolares_mes=r.gastos_dolares_periodo,
            objetivos=[ObjetivoSalida.desde(o.objetivo, o.apartado) for o in r.objetivos],
            deuda_tarjetas=r.deuda_tarjetas,
            proximo_resumen_tarjetas=r.proximo_resumen_tarjetas,
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


# -- Tarjetas de crédito ----------------------------------------------------


class TarjetaEntrada(BaseModel):
    nombre: str = Field(max_length=60)
    dia_cierre: int
    dia_vencimiento: int


class TarjetaCambios(BaseModel):
    nombre: str | None = Field(default=None, max_length=60)
    dia_cierre: int | None = None
    dia_vencimiento: int | None = None
    activa: bool | None = None


class MesMonto(BaseModel):
    mes: date
    monto: Monto


class TarjetaSalida(BaseModel):
    id: UUID
    nombre: str
    dia_cierre: int
    dia_vencimiento: int
    activa: bool
    deuda_estimada: Monto
    resumen_cerrado: Monto
    resumen_en_curso: Monto
    mes_en_curso: date
    proximos: list[MesMonto]

    @classmethod
    def desde(cls, e: EstadoTarjeta) -> "TarjetaSalida":
        t = e.tarjeta
        return cls(
            id=t.id,
            nombre=t.nombre,
            dia_cierre=t.dia_cierre,
            dia_vencimiento=t.dia_vencimiento,
            activa=t.activa,
            deuda_estimada=e.deuda_estimada,
            resumen_cerrado=e.resumen_cerrado,
            resumen_en_curso=e.resumen_en_curso,
            mes_en_curso=e.mes_en_curso,
            proximos=[MesMonto(mes=mes, monto=monto) for mes, monto in e.proximos],
        )


class CompraTarjetaEntrada(BaseModel):
    monto: Monto
    cuotas: int = 1
    comprado_en: date
    categoria_id: UUID | None = None
    descripcion: str | None = Field(default=None, max_length=200)
    # Lo genera el dispositivo: si la misma carga llega dos veces, se devuelve lo ya guardado
    id_carga: UUID | None = None


class CuotaSalida(BaseModel):
    numero: int
    monto: Monto
    mes_resumen: date


class CompraTarjetaSalida(BaseModel):
    id: UUID
    tarjeta_id: UUID
    descripcion: str | None
    categoria_id: UUID | None
    monto_total: Monto
    cantidad_cuotas: int
    comprado_en: date
    cuotas: list[CuotaSalida]

    @classmethod
    def desde(cls, c: CompraTarjeta) -> "CompraTarjetaSalida":
        return cls(
            id=c.id,
            tarjeta_id=c.tarjeta_id,
            descripcion=c.descripcion,
            categoria_id=c.categoria_id,
            monto_total=c.monto_total,
            cantidad_cuotas=c.cantidad_cuotas,
            comprado_en=c.comprado_en,
            cuotas=[CuotaSalida(numero=q.numero, monto=q.monto, mes_resumen=q.mes_resumen) for q in c.cuotas],
        )


class PagoResumenEntrada(BaseModel):
    monto: Monto
    ocurrido_en: datetime
    origenes: list[OrigenEntrada] | None = Field(default=None, max_length=10)
