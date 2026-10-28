import { ChangeDetectionStrategy, Component, computed, input, output } from '@angular/core';

import { Movimiento } from '../../nucleo/modelos';
import { MontoPipe } from '../monto.pipe';

/** Un renglón de la lista de movimientos. Presentacional: recibe los nombres ya resueltos. */
@Component({
  selector: 'bi-fila-movimiento',
  imports: [MontoPipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <span class="icono" [class]="clase()" aria-hidden="true">{{ inicial() }}</span>
    <span class="texto">
      <span class="titulo">{{ titulo() }}</span>
      <span class="detalle">{{ detalle() }}</span>
    </span>
    <span class="num monto" [class]="clase()">
      @if (movimiento().tipo === 'transferencia') { ↔ {{ movimiento().monto | monto }} }
      @else { {{ montoConSigno() | monto: 'signo' }} }
    </span>
    @if (eliminable()) {
      <button type="button" class="boton boton-icono" (click)="eliminar.emit()" [attr.aria-label]="'Eliminar ' + titulo()">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 7h14M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3" /></svg>
      </button>
    }
  `,
  styles: `
    :host { display: flex; align-items: center; gap: 12px; padding: 10px 0; }
    .icono {
      width: 40px; height: 40px; flex: none; border-radius: var(--radio-icono);
      display: flex; align-items: center; justify-content: center; font-weight: 600;
    }
    .icono.gasto { background: var(--gasto-fondo); }
    .icono.ingreso { background: var(--ingreso-fondo); }
    .icono.transferencia { background: var(--relleno); }
    .texto { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
    .titulo { font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .detalle { font-size: 12px; color: var(--atenuado); }
    .monto.transferencia { color: var(--atenuado); }
    svg { width: 18px; height: 18px; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
  `,
})
export class FilaMovimientoComponent {
  readonly movimiento = input.required<Movimiento>();
  readonly nombreCategoria = input<string | null>(null);
  readonly nombreMetodo = input<string | null>(null);
  readonly eliminable = input(false);
  readonly eliminar = output<void>();

  readonly clase = computed(() => this.movimiento().tipo);

  readonly titulo = computed(() => {
    const m = this.movimiento();
    if (m.descripcion) return m.descripcion;
    if (this.nombreCategoria()) return this.nombreCategoria()!;
    if (m.tipo === 'transferencia') return descripcionTransferencia(m);
    return m.tipo === 'gasto' ? 'Gasto' : 'Ingreso';
  });

  readonly inicial = computed(() => this.titulo().charAt(0).toUpperCase());

  readonly detalle = computed(() => {
    const m = this.movimiento();
    if (m.tipo === 'transferencia') return 'Transferencia · no cuenta como gasto';
    if (m.tarjeta_id) return 'Pago de tarjeta de crédito';
    const partes = [this.nombreCategoria() ?? (m.tipo === 'gasto' ? 'Gasto' : 'Ingreso')];
    if (m.tipo === 'gasto' && m.partes.length > 1) partes.push(origenesDeGasto(m));
    else if (m.tipo === 'gasto' && m.partes[0]?.bolsillo === 'ahorros') partes.push('Pagado con ahorros');
    else if (this.nombreMetodo()) partes.push(this.nombreMetodo()!);
    return partes.join(' · ');
  });

  readonly montoConSigno = computed(() => {
    const m = this.movimiento();
    return m.tipo === 'gasto' ? -Number(m.monto) : Number(m.monto);
  });
}

function descripcionTransferencia(m: Movimiento): string {
  const destino = m.partes.find((p) => Number(p.monto) > 0);
  const origen = m.partes.find((p) => Number(p.monto) < 0);
  if (destino?.objetivo_id) return 'Apartado para un objetivo';
  if (origen?.objetivo_id) return 'Devuelto a ahorros';
  return destino?.bolsillo === 'ahorros' ? 'Mandaste a ahorros' : 'Pasaste a disponible';
}

function origenesDeGasto(m: Movimiento): string {
  const usaMes = m.partes.some((p) => p.bolsillo === 'disponible');
  const usaAhorros = m.partes.some((p) => p.bolsillo === 'ahorros');
  return usaMes && usaAhorros ? 'Plata del mes + ahorros' : 'Dividido';
}
