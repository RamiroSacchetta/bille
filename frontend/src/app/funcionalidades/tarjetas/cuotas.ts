// Ayudas de presentación para compras en cuotas.

import { formatearMonto } from '../../nucleo/formato';
import { CompraTarjeta } from '../../nucleo/modelos';

/** "3 cuotas de $ 300.000" o "1 pago de $ 50.000". Es una vista previa: el reparto exacto lo hace el backend. */
export function textoCuotas(monto: number, cuotas: number): string {
  if (!monto || cuotas < 1) return '';
  const valor = formatearMonto(Math.floor((monto / cuotas) * 100) / 100);
  return cuotas === 1 ? `1 pago de ${valor}` : `${cuotas} cuotas de ${valor}`;
}

/** Número de la cuota que corresponde al resumen en curso: "Cuota 2 de 3". */
export function cuotaActual(compra: CompraTarjeta, mesEnCurso: string): number {
  const vencidas = compra.cuotas.filter((c) => c.mes_resumen <= mesEnCurso).length;
  return Math.min(Math.max(vencidas, 1), compra.cantidad_cuotas);
}

/** "nov 2026" a partir de "2026-11-01". */
export function mesCorto(mes: string): string {
  const [anio, numero] = mes.split('-').map(Number);
  return new Intl.DateTimeFormat('es-AR', { month: 'short', year: 'numeric' })
    .format(new Date(anio, numero - 1, 1))
    .replace(' de ', ' ')
    .replace('.', '');
}
