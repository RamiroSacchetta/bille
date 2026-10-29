// Lógica del pago dividido, separada de la pantalla para poder probarla sola.

import { formatearMonto } from '../../nucleo/formato';
import { Bolsillo, Moneda, Resumen } from '../../nucleo/modelos';

export interface Origen {
  clave: string;
  nombre: string;
  bolsillo: Bolsillo;
  objetivo_id: string | null;
  saldo: number;
}

export interface EstadoDivision {
  asignado: number;
  falta: number;
  cuadra: boolean;
  mensaje: string;
}

/** Compara lo asignado a cada origen con el total del gasto. */
export function estadoDivision(total: number, montos: Record<string, number>, moneda: Moneda = 'ARS'): EstadoDivision {
  const asignado = Object.values(montos).reduce((suma, monto) => suma + (monto || 0), 0);
  const falta = Math.round((total - asignado) * 100) / 100;
  let mensaje = `Listo: las partes suman ${formatearMonto(total, moneda)}`;
  if (falta > 0) mensaje = `Falta asignar ${formatearMonto(falta, moneda)}`;
  if (falta < 0) mensaje = `Te pasaste por ${formatearMonto(falta, moneda)}`;
  return { asignado, falta, cuadra: falta === 0 && total > 0, mensaje };
}

/** De dónde puede salir un gasto: en pesos o en dólares, nunca mezclados. */
export function origenesDeGasto(resumen: Resumen | null, moneda: Moneda): Origen[] {
  if (!resumen) return [];
  const objetivos = resumen.objetivos
    .filter((o) => o.moneda === moneda)
    .map((o) => ({
      clave: o.id,
      nombre: o.nombre,
      bolsillo: (moneda === 'USD' ? 'dolares' : 'ahorros') as Bolsillo,
      objetivo_id: o.id,
      saldo: Number(o.apartado),
    }));
  if (moneda === 'USD') {
    return [
      { clave: 'dolares', nombre: 'Dólares libres', bolsillo: 'dolares', objetivo_id: null, saldo: Number(resumen.saldos.dolares_libres) },
      ...objetivos,
    ];
  }
  return [
    { clave: 'mes', nombre: 'Plata del mes', bolsillo: 'disponible', objetivo_id: null, saldo: Number(resumen.saldos.disponible) },
    { clave: 'libre', nombre: 'Ahorro libre', bolsillo: 'ahorros', objetivo_id: null, saldo: Number(resumen.saldos.ahorro_libre) },
    ...objetivos,
  ];
}

/** Orígenes con monto mayor a cero, listos para mandar a la API. */
export function origenesParaApi(origenes: Origen[], montos: Record<string, number>) {
  return origenes
    .filter((origen) => (montos[origen.clave] ?? 0) > 0)
    .map((origen) => ({
      bolsillo: origen.bolsillo,
      objetivo_id: origen.objetivo_id,
      monto: montos[origen.clave].toFixed(2),
    }));
}
