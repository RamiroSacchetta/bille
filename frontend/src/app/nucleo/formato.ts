// Formato de montos y fechas en es-AR.

import { Moneda, Movimiento } from './modelos';

const pesos = new Intl.NumberFormat('es-AR', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
const pesosConDecimales = new Intl.NumberFormat('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const simbolos: Record<Moneda, string> = { ARS: '$ ', USD: 'US$ ' };

/** "$ 1.250.000" o "US$ 1.500" — con `decimales` siempre muestra dos decimales. */
export function formatearMonto(monto: string | number, moneda: Moneda = 'ARS', decimales = false): string {
  const valor = Math.abs(Number(monto));
  return simbolos[moneda] + (decimales ? pesosConDecimales : pesos).format(valor);
}

/** Monto con signo tipográfico: "+$ 1.000", "−US$ 500". */
export function formatearConSigno(monto: string | number, moneda: Moneda = 'ARS'): string {
  const valor = Number(monto);
  return (valor < 0 ? '−' : '+') + formatearMonto(valor, moneda);
}

/** Pesos por cada dólar, redondeado a centavos; null si falta alguno de los dos montos. */
export function precioPorDolar(dolares: number, pesos: number): number | null {
  if (!(dolares > 0) || !(pesos > 0)) return null;
  return Math.round((pesos / dolares) * 100) / 100;
}

/** "Compraste US$ 200" y "$ 240.000 · $ 1.200 por dólar" para un movimiento de cambio. */
export function textosCambio(m: Movimiento): { titulo: string; detalle: string } {
  const dolares = Number(m.partes.find((p) => p.bolsillo === 'dolares')?.monto ?? 0);
  // Los pesos son la parte que no es de dólares, con el signo opuesto
  const pesos = Math.abs(Number(m.partes.find((p) => p.bolsillo !== 'dolares')?.monto ?? 0));
  const verbo = dolares < 0 ? 'Vendiste' : 'Compraste';
  const precio = precioPorDolar(Math.abs(dolares), pesos);
  const detalle = [formatearMonto(pesos), ...(precio ? [`${formatearMonto(precio)} por dólar`] : [])].join(' · ');
  return { titulo: `${verbo} ${formatearMonto(m.monto, 'USD')}`, detalle };
}

/** "2026-10" para el mes de la fecha dada. */
export function claveMes(fecha = new Date()): string {
  return `${fecha.getFullYear()}-${String(fecha.getMonth() + 1).padStart(2, '0')}`;
}

/** Mueve una clave de mes "2026-10" n meses. */
export function moverMes(clave: string, n: number): string {
  const [anio, mes] = clave.split('-').map(Number);
  return claveMes(new Date(anio, mes - 1 + n, 1));
}

/** "Octubre 2026" */
export function nombreMes(clave: string): string {
  const [anio, mes] = clave.split('-').map(Number);
  const texto = new Intl.DateTimeFormat('es-AR', { month: 'long', year: 'numeric' }).format(new Date(anio, mes - 1, 1));
  return texto.charAt(0).toUpperCase() + texto.slice(1).replace(' de ', ' ');
}

/** "Hoy", "Ayer" o "lun 26 oct" para agrupar movimientos por día. */
export function nombreDia(fecha: Date, hoy = new Date()): string {
  const dia = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
  const diferencia = Math.round((dia(hoy) - dia(fecha)) / 86_400_000);
  if (diferencia === 0) return 'Hoy';
  if (diferencia === 1) return 'Ayer';
  return new Intl.DateTimeFormat('es-AR', { weekday: 'short', day: 'numeric', month: 'short' }).format(fecha);
}

/** Convierte lo que escribe el usuario ("1.250.000,50") a texto numérico para la API ("1250000.50"). */
export function montoDesdeTexto(texto: string): string | null {
  const limpio = texto.replace(/\s|\$/g, '').replace(/\./g, '').replace(',', '.');
  if (!/^\d+(\.\d{1,2})?$/.test(limpio) || Number(limpio) <= 0) return null;
  return limpio;
}

/** Fecha local "2026-10-28" a ISO con la hora actual, para `ocurrido_en`. */
export function fechaParaApi(fechaLocal: string): string {
  const ahora = new Date();
  const [anio, mes, dia] = fechaLocal.split('-').map(Number);
  return new Date(anio, mes - 1, dia, ahora.getHours(), ahora.getMinutes(), ahora.getSeconds()).toISOString();
}

export function hoyLocal(): string {
  const hoy = new Date();
  return `${hoy.getFullYear()}-${String(hoy.getMonth() + 1).padStart(2, '0')}-${String(hoy.getDate()).padStart(2, '0')}`;
}
