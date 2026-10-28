// Lógica del pago dividido, separada de la pantalla para poder probarla sola.

import { Bolsillo } from '../../nucleo/modelos';

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
export function estadoDivision(total: number, montos: Record<string, number>): EstadoDivision {
  const asignado = Object.values(montos).reduce((suma, monto) => suma + (monto || 0), 0);
  const falta = Math.round((total - asignado) * 100) / 100;
  const formato = new Intl.NumberFormat('es-AR', { maximumFractionDigits: 2 });
  let mensaje = `Listo: las partes suman $ ${formato.format(total)}`;
  if (falta > 0) mensaje = `Falta asignar $ ${formato.format(falta)}`;
  if (falta < 0) mensaje = `Te pasaste por $ ${formato.format(-falta)}`;
  return { asignado, falta, cuadra: falta === 0 && total > 0, mensaje };
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
