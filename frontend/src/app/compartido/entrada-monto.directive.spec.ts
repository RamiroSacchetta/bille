import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';

import { EntradaMontoDirective } from './entrada-monto.directive';

@Component({
  imports: [FormsModule, EntradaMontoDirective],
  template: `<input name="monto" biMonto [(ngModel)]="monto" />`,
})
class AnfitrionComponent {
  monto = '';
}

describe('EntradaMontoDirective', () => {
  function escribir(campo: HTMLInputElement, valor: string, dato: string | null = valor.slice(-1)): void {
    campo.value = valor;
    campo.setSelectionRange(valor.length, valor.length);
    campo.dispatchEvent(new InputEvent('input', { data: dato, bubbles: true }));
  }

  async function montar() {
    const fixture = TestBed.createComponent(AnfitrionComponent);
    fixture.detectChanges();
    await fixture.whenStable();
    const campo: HTMLInputElement = fixture.nativeElement.querySelector('input');
    return { fixture, campo };
  }

  it('pone los puntos de miles y le pasa el texto formateado a ngModel', async () => {
    const { fixture, campo } = await montar();
    escribir(campo, '1250000');
    expect(campo.value).toBe('1.250.000');
    expect(fixture.componentInstance.monto).toBe('1.250.000');
  });

  it('toma un punto tipeado como la coma de los centavos', async () => {
    const { fixture, campo } = await montar();
    escribir(campo, '1.250.');
    expect(campo.value).toBe('1.250,');
    escribir(campo, '1.250,5');
    expect(fixture.componentInstance.monto).toBe('1.250,5');
  });

  it('no deja escribir más de dos centavos', async () => {
    const { campo } = await montar();
    escribir(campo, '1.250,567');
    expect(campo.value).toBe('1.250,56');
  });
});
