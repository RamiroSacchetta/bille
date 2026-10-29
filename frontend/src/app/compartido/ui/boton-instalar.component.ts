import { ChangeDetectionStrategy, Component, inject, input, signal } from '@angular/core';

import { InstalacionServicio } from '../../nucleo/instalacion';

/** Ofrece instalar Bille cuando se abre desde el navegador: un botón en Android y PC, y los pasos en iPhone. */
@Component({
  selector: 'bi-boton-instalar',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @switch (instalacion.modo()) {
      @case ('boton') {
        <button type="button" class="boton boton-primario boton-ancho" [class.sobre-oscuro]="sobreOscuro()" (click)="instalacion.instalar()">Instalar Bille</button>
      }
      @case ('ios') {
        <button type="button" class="boton boton-ancho" [class.sobre-oscuro]="sobreOscuro()" [attr.aria-expanded]="verPasos()" (click)="verPasos.set(!verPasos())">
          Instalar Bille
        </button>
        @if (verPasos()) {
          <p class="pasos">En Safari, tocá <strong>Compartir</strong> (el cuadrado con la flecha) y después <strong>Agregar a inicio</strong>.</p>
        }
      }
    }
  `,
  styles: `
    :host { display: block; }
    :host:empty { display: none; }
    .pasos { margin: 8px 0 0; font-size: 14px; line-height: 1.4; }
    .sobre-oscuro { background: var(--lima); color: var(--bosque); border-color: var(--lima); }
  `,
})
export class BotonInstalarComponent {
  readonly instalacion = inject(InstalacionServicio);
  /** En la pantalla de ingreso, sobre el fondo verde oscuro. */
  readonly sobreOscuro = input(false);
  readonly verPasos = signal(false);
}
