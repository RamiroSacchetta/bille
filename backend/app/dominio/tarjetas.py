"""Tarjetas de crédito.

Comprar con tarjeta no mueve plata: genera cuotas que se acumulan como deuda estimada en la tarjeta.
Lo anotado es aproximado (el usuario puede olvidarse de cargar algo); el dato real es el pago del resumen,
que es un gasto común y baja la deuda.
"""

import calendar
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_DOWN, Decimal
from uuid import UUID

from app.dominio.errores import DatosInvalidos


@dataclass
class Tarjeta:
    usuario_id: UUID
    nombre: str
    dia_cierre: int
    dia_vencimiento: int
    activa: bool = True
    id: UUID | None = None


@dataclass(frozen=True)
class Cuota:
    numero: int
    monto: Decimal
    mes_resumen: date


@dataclass
class CompraTarjeta:
    usuario_id: UUID
    tarjeta_id: UUID
    monto_total: Decimal
    cantidad_cuotas: int
    comprado_en: date
    cuotas: list[Cuota]
    descripcion: str | None = None
    categoria_id: UUID | None = None
    id: UUID | None = None


@dataclass(frozen=True)
class EstadoTarjeta:
    tarjeta: Tarjeta
    deuda_estimada: Decimal
    resumen_cerrado: Decimal
    resumen_en_curso: Decimal
    mes_en_curso: date
    proximos: list[tuple[date, Decimal]] = field(default_factory=list)
    # Lo que falta pagar del próximo resumen, el que se suele pagar con el sueldo que viene
    proximo_resumen: Decimal = Decimal(0)


def validar_dia(dia: int, nombre: str) -> int:
    if not 1 <= dia <= 31:
        raise DatosInvalidos(f"El día de {nombre} tiene que estar entre 1 y 31")
    return dia


def sumar_meses(mes: date, cantidad: int) -> date:
    indice = mes.year * 12 + (mes.month - 1) + cantidad
    return date(indice // 12, indice % 12 + 1, 1)


def mes_de_resumen(fecha: date, dia_cierre: int) -> date:
    """Mes del resumen donde cae una compra: hasta el día de cierre es ese mes, después el siguiente.

    Si el mes tiene menos días que el día de cierre (por ejemplo 31 en febrero), cierra el último día.
    """
    ultimo_dia = calendar.monthrange(fecha.year, fecha.month)[1]
    mes = date(fecha.year, fecha.month, 1)
    return mes if fecha.day <= min(dia_cierre, ultimo_dia) else sumar_meses(mes, 1)


def dividir_en_cuotas(total: Decimal, cantidad: int, primer_mes: date) -> list[Cuota]:
    """Reparte el total en cuotas iguales; los centavos que sobran van en la primera."""
    if not 1 <= cantidad <= 60:
        raise DatosInvalidos("Las cuotas tienen que ser entre 1 y 60")
    base = (total / cantidad).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    if base <= 0:
        raise DatosInvalidos("El monto es muy chico para esa cantidad de cuotas")
    resto = total - base * cantidad
    return [
        Cuota(numero, base + (resto if numero == 1 else 0), sumar_meses(primer_mes, numero - 1))
        for numero in range(1, cantidad + 1)
    ]


def proximo_resumen(cuotas_por_mes: dict[date, Decimal], pagado: Decimal, cerrado: date) -> Decimal:
    """Lo que falta pagar del próximo resumen.

    Los pagos cubren primero los resúmenes más viejos. Mientras quede algo del último resumen cerrado
    (o de los anteriores), el próximo es ese; si ya está pago, el primero que tenga cuotas pendientes.
    """
    restante = pagado
    pendientes: list[tuple[date, Decimal]] = []
    for mes in sorted(cuotas_por_mes):
        cubierto = min(restante, cuotas_por_mes[mes])
        restante -= cubierto
        if cuotas_por_mes[mes] > cubierto:
            pendientes.append((mes, cuotas_por_mes[mes] - cubierto))
    if not pendientes:
        return Decimal(0)
    hasta = max(cerrado, pendientes[0][0])
    return sum((monto for mes, monto in pendientes if mes <= hasta), Decimal(0))


def calcular_estado(
    tarjeta: Tarjeta, cuotas_por_mes: dict[date, Decimal], pagado: Decimal, hoy: date, meses_proximos: int = 6
) -> EstadoTarjeta:
    """Resume la tarjeta: deuda estimada, último resumen cerrado, el que está en curso y los que vienen."""
    anotado = sum(cuotas_por_mes.values(), Decimal(0))
    en_curso = mes_de_resumen(hoy, tarjeta.dia_cierre)
    return EstadoTarjeta(
        tarjeta=tarjeta,
        deuda_estimada=max(anotado - pagado, Decimal(0)),
        resumen_cerrado=cuotas_por_mes.get(sumar_meses(en_curso, -1), Decimal(0)),
        resumen_en_curso=cuotas_por_mes.get(en_curso, Decimal(0)),
        mes_en_curso=en_curso,
        proximos=[
            (mes, cuotas_por_mes[mes])
            for mes in (sumar_meses(en_curso, n) for n in range(1, meses_proximos + 1))
            if mes in cuotas_por_mes
        ],
        proximo_resumen=proximo_resumen(cuotas_por_mes, pagado, sumar_meses(en_curso, -1)),
    )
