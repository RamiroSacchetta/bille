import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

/** Barra de progreso de un objetivo; `sobreOscuro` para usarla dentro de las tarjetas destacadas. */
@Component({
  selector: 'bi-barra-progreso',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <span class="pista" [class.oscura]="sobreOscuro()" role="progressbar" [attr.aria-valuenow]="porcentaje()"
      aria-valuemin="0" aria-valuemax="100" [attr.aria-label]="etiqueta()">
      <span class="relleno" [style.width.%]="porcentaje()"></span>
    </span>
  `,
  styles: `
    .pista { display: block; height: 8px; border-radius: 4px; background: var(--linea); overflow: hidden; }
    .pista.oscura { height: 12px; border-radius: 6px; background: var(--bosque-3); }
    .relleno { display: block; height: 100%; border-radius: inherit; background: var(--bosque); }
    .oscura .relleno { background: var(--lima); }
  `,
})
export class BarraProgresoComponent {
  readonly actual = input.required<string | number>();
  readonly meta = input.required<string | number>();
  readonly etiqueta = input('Progreso');
  readonly sobreOscuro = input(false);

  readonly porcentaje = computed(() => {
    const meta = Number(this.meta());
    if (meta <= 0) return 0;
    return Math.max(0, Math.min(100, Math.round((Number(this.actual()) / meta) * 100)));
  });
}
