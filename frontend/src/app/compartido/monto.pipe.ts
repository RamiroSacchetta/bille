import { Pipe, PipeTransform } from '@angular/core';

import { formatearConSigno, formatearMonto } from '../nucleo/formato';

/** {{ '1250000' | monto }} → "$ 1.250.000"; con 'signo' → "+$ 1.250.000". */
@Pipe({ name: 'monto' })
export class MontoPipe implements PipeTransform {
  transform(valor: string | number | null | undefined, modo: 'simple' | 'signo' | 'decimales' = 'simple'): string {
    if (valor === null || valor === undefined) return '';
    if (modo === 'signo') return formatearConSigno(valor);
    return formatearMonto(valor, modo === 'decimales');
  }
}
