import { Pipe, PipeTransform } from '@angular/core';

import { formatearConSigno, formatearMonto } from '../nucleo/formato';
import { Moneda } from '../nucleo/modelos';

/**
 * {{ '1250000' | monto }} → "$ 1.250.000"; con 'signo' → "+$ 1.250.000"; con moneda 'USD' → "US$ 1.250.000".
 * No es puro: la moneda principal puede cambiar desde Ajustes sin que cambie el monto.
 */
@Pipe({ name: 'monto', pure: false })
export class MontoPipe implements PipeTransform {
  transform(
    valor: string | number | null | undefined,
    modo: 'simple' | 'signo' | 'decimales' = 'simple',
    moneda: Moneda = 'ARS',
  ): string {
    if (valor === null || valor === undefined) return '';
    if (modo === 'signo') return formatearConSigno(valor, moneda);
    return formatearMonto(valor, moneda, modo === 'decimales');
  }
}
