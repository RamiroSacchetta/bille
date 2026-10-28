import { ChangeDetectionStrategy, Component, OnInit, computed, inject, signal } from '@angular/core';

import { MontoPipe } from '../../compartido/monto.pipe';
import { FilaMovimientoComponent } from '../../compartido/ui/fila-movimiento.component';
import { NavegacionComponent } from '../../compartido/ui/navegacion.component';
import { ApiServicio, mensajeDeError } from '../../nucleo/api.servicio';
import { CatalogoStore } from '../../nucleo/catalogo.store';
import { claveMes, moverMes, nombreDia, nombreMes } from '../../nucleo/formato';
import { Movimiento } from '../../nucleo/modelos';

type Filtro = 'todos' | 'gasto' | 'ingreso';

interface Dia {
  nombre: string;
  neto: number;
  movimientos: Movimiento[];
}

/** Lista de movimientos del mes, agrupada por día, con filtro y opción de eliminar. */
@Component({
  selector: 'bi-movimientos',
  imports: [MontoPipe, FilaMovimientoComponent, NavegacionComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <main class="pantalla">
      <header class="encabezado">
        <h1>Movimientos</h1>
        <button type="button" class="boton" (click)="exportar()" [disabled]="exportando()">Exportar CSV</button>
      </header>

      <div class="selector-mes tarjeta">
        <button type="button" class="boton boton-icono" (click)="cambiarMes(-1)" aria-label="Mes anterior">‹</button>
        <span>{{ nombreMes(mes()) }}</span>
        <button type="button" class="boton boton-icono" (click)="cambiarMes(1)" aria-label="Mes siguiente">›</button>
      </div>

      <div class="chips" role="group" aria-label="Filtro">
        @for (opcion of filtros; track opcion.valor) {
          <button type="button" class="chip" [attr.aria-pressed]="filtro() === opcion.valor" (click)="filtro.set(opcion.valor)">
            {{ opcion.texto }}
          </button>
        }
      </div>

      @if (error()) { <p class="error" role="alert">{{ error() }}</p> }

      @for (dia of dias(); track dia.nombre) {
        <section class="seccion dia">
          <div class="cabecera-dia">
            <span>{{ dia.nombre }}</span>
            <span class="num">{{ dia.neto | monto: 'signo' }}</span>
          </div>
          <ul class="lista">
            @for (m of dia.movimientos; track m.id) {
              <li>
                <bi-fila-movimiento [movimiento]="m" [eliminable]="true" (eliminar)="pedirConfirmacion(m)"
                  [nombreCategoria]="catalogo.nombresCategoria().get(m.categoria_id ?? '') ?? null"
                  [nombreMetodo]="catalogo.nombresMetodo().get(m.metodo_pago_id ?? '') ?? null" />
                @if (aConfirmar()?.id === m.id) {
                  <div class="confirmar" role="alert">
                    <span>¿Eliminar este movimiento?</span>
                    <button type="button" class="boton" (click)="aConfirmar.set(null)">Cancelar</button>
                    <button type="button" class="boton boton-peligro" (click)="eliminar(m)">Eliminar</button>
                  </div>
                }
              </li>
            }
          </ul>
        </section>
      } @empty {
        <p class="vacio">No hay movimientos para mostrar en este mes.</p>
      }
    </main>
    <bi-navegacion />
  `,
  styles: `
    .selector-mes { display: flex; align-items: center; justify-content: space-between; padding: 6px; font-weight: 600; }
    .selector-mes .boton { border: 0; }
    .dia { gap: 6px; }
    .cabecera-dia { display: flex; justify-content: space-between; font-size: 13px; font-weight: 600; color: var(--atenuado); padding: 0 4px; }
    .confirmar { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; padding: 0 0 12px; font-size: 14px; }
    .confirmar span { flex: 1; min-width: 160px; }
  `,
})
export class MovimientosPagina implements OnInit {
  private readonly api = inject(ApiServicio);
  readonly catalogo = inject(CatalogoStore);

  readonly filtros: { valor: Filtro; texto: string }[] = [
    { valor: 'todos', texto: 'Todos' },
    { valor: 'gasto', texto: 'Gastos' },
    { valor: 'ingreso', texto: 'Ingresos' },
  ];
  readonly mes = signal(claveMes());
  readonly filtro = signal<Filtro>('todos');
  readonly movimientos = signal<Movimiento[]>([]);
  readonly aConfirmar = signal<Movimiento | null>(null);
  readonly exportando = signal(false);
  readonly error = signal<string | null>(null);
  readonly nombreMes = nombreMes;

  readonly dias = computed<Dia[]>(() => {
    const filtro = this.filtro();
    const dias = new Map<string, Dia>();
    for (const m of this.movimientos()) {
      if (filtro !== 'todos' && m.tipo !== filtro) continue;
      const nombre = nombreDia(new Date(m.ocurrido_en));
      const dia = dias.get(nombre) ?? { nombre, neto: 0, movimientos: [] };
      // Las transferencias no suman ni restan al balance del día
      if (m.tipo === 'ingreso') dia.neto += Number(m.monto);
      if (m.tipo === 'gasto') dia.neto -= Number(m.monto);
      dia.movimientos.push(m);
      dias.set(nombre, dia);
    }
    return [...dias.values()];
  });

  ngOnInit(): void {
    this.catalogo.cargar();
    this.cargar();
  }

  cambiarMes(delta: number): void {
    this.mes.update((mes) => moverMes(mes, delta));
    this.cargar();
  }

  /** Descarga el CSV del mes elegido para abrirlo en Excel. */
  exportar(): void {
    this.exportando.set(true);
    this.api.exportarMovimientos(this.mes()).subscribe({
      next: (archivo) => {
        const url = URL.createObjectURL(archivo);
        const enlace = document.createElement('a');
        enlace.href = url;
        enlace.download = `bille-movimientos-${this.mes()}.csv`;
        enlace.click();
        URL.revokeObjectURL(url);
        this.exportando.set(false);
      },
      error: (error) => {
        this.exportando.set(false);
        this.error.set(mensajeDeError(error));
      },
    });
  }

  pedirConfirmacion(movimiento: Movimiento): void {
    this.aConfirmar.set(movimiento);
  }

  eliminar(movimiento: Movimiento): void {
    this.api.eliminarMovimiento(movimiento.id).subscribe({
      next: () => {
        this.aConfirmar.set(null);
        this.movimientos.update((lista) => lista.filter((m) => m.id !== movimiento.id));
      },
      error: (error) => {
        this.aConfirmar.set(null);
        this.error.set(mensajeDeError(error));
      },
    });
  }

  private cargar(): void {
    this.error.set(null);
    this.api.movimientos({ mes: this.mes() }).subscribe({
      next: (movimientos) => this.movimientos.set(movimientos),
      error: (error) => this.error.set(mensajeDeError(error)),
    });
  }
}
