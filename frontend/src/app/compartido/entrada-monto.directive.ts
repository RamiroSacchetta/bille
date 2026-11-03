import { Directive, ElementRef, HostListener, inject } from '@angular/core';

import { formatearEntradaMonto } from '../nucleo/formato';

/**
 * Formatea un campo de monto mientras se escribe: "1.250.000,50".
 * Mantiene el cursor en el mismo dígito y avisa el valor formateado a `ngModel`.
 */
@Directive({ selector: 'input[biMonto]' })
export class EntradaMontoDirective {
  private readonly campo: HTMLInputElement = inject(ElementRef).nativeElement;

  @HostListener('input', ['$event'])
  alEscribir(evento: Event): void {
    let valor = this.campo.value;
    const cursor = this.campo.selectionStart ?? valor.length;

    // Los puntos los pone la app: un punto tipeado es la intención de escribir centavos
    // (hay teclados numéricos de celular que no tienen coma)
    if ((evento as InputEvent).data === '.' && !valor.includes(',') && valor[cursor - 1] === '.') {
      valor = valor.slice(0, cursor - 1) + ',' + valor.slice(cursor);
    }

    const formateado = formatearEntradaMonto(valor);
    if (formateado === this.campo.value) return;

    // Ubica el cursor después de la misma cantidad de dígitos (y coma) que tenía antes
    const significativos = valor.slice(0, cursor).replace(/[^\d,]/g, '').length;
    let posicion = 0;
    for (let vistos = 0; posicion < formateado.length && vistos < significativos; posicion++) {
      if (/[\d,]/.test(formateado[posicion])) vistos++;
    }

    this.campo.value = formateado;
    this.campo.setSelectionRange(posicion, posicion);
    // Un segundo evento para que ngModel reciba el texto ya formateado
    this.campo.dispatchEvent(new Event('input', { bubbles: true }));
  }
}
