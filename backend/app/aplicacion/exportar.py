"""Exportación de movimientos a CSV, pensado para abrir en Excel con configuración regional es-AR."""

import csv
import io
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo

from app.dominio.modelos import Bolsillo, Movimiento, TipoMovimiento

ENCABEZADOS = ["Fecha", "Tipo", "Descripción", "Categoría", "Método de pago", "Monto", "De dónde / a dónde"]
# Marca de orden de bytes: Excel la usa para detectar UTF-8
BOM = chr(0xFEFF)
TIPOS = {
    TipoMovimiento.INGRESO: "Ingreso",
    TipoMovimiento.GASTO: "Gasto",
    TipoMovimiento.TRANSFERENCIA: "Transferencia",
}


def numero(valor: Decimal) -> str:
    """1250000.5 → '1250000,50': sin separador de miles y con coma decimal, como lo espera Excel en es-AR."""
    return f"{valor:.2f}".replace(".", ",")


def _ubicacion(bolsillo: Bolsillo, objetivo_id: UUID | None, objetivos: dict[UUID, str]) -> str:
    if bolsillo is Bolsillo.DISPONIBLE:
        return "Plata del mes"
    if objetivo_id is None:
        return "Ahorro libre"
    return objetivos.get(objetivo_id, "Objetivo")


def movimientos_a_csv(
    movimientos: list[Movimiento],
    categorias: dict[UUID, str],
    metodos: dict[UUID, str],
    objetivos: dict[UUID, str],
    tarjetas: dict[UUID, str],
    zona_horaria: str,
) -> str:
    zona = ZoneInfo(zona_horaria)
    salida = io.StringIO()
    # BOM para que Excel detecte UTF-8 y muestre bien los acentos
    salida.write(BOM)
    escritor = csv.writer(salida, delimiter=";", lineterminator="\r\n")
    escritor.writerow(ENCABEZADOS)
    for m in sorted(movimientos, key=lambda m: m.ocurrido_en):
        signo = -1 if m.tipo is TipoMovimiento.GASTO else 1
        metodo = tarjetas.get(m.tarjeta_id) if m.tarjeta_id else metodos.get(m.metodo_pago_id, "")
        partes = " | ".join(
            f"{_ubicacion(p.ubicacion.bolsillo, p.ubicacion.objetivo_id, objetivos)} {numero(p.monto)}"
            for p in m.partes
        )
        escritor.writerow(
            [
                m.ocurrido_en.astimezone(zona).strftime("%d/%m/%Y"),
                TIPOS[m.tipo],
                m.descripcion or "",
                categorias.get(m.categoria_id, "") if m.categoria_id else "",
                metodo or "",
                numero(m.monto * signo),
                partes,
            ]
        )
    return salida.getvalue()
