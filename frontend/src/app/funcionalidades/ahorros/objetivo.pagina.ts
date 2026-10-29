import { ChangeDetectionStrategy, Component, OnInit, computed, inject, input, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { MontoPipe } from '../../compartido/monto.pipe';
import { BarraProgresoComponent } from '../../compartido/ui/barra-progreso.component';
import { ApiServicio, mensajeDeError } from '../../nucleo/api.servicio';
import { claveMes, fechaParaApi, hoyLocal, montoDesdeTexto, nombreDia } from '../../nucleo/formato';
import { Movimiento, Objetivo, Resumen } from '../../nucleo/modelos';

type Modo = 'apartar' | 'devolver';

/** Detalle de un objetivo: lo apartado, apartar desde el ahorro libre o devolver, y su historial. */
@Component({
  selector: 'bi-objetivo',
  imports: [FormsModule, RouterLink, MontoPipe, BarraProgresoComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <main class="pantalla">
      <header class="encabezado">
        <a routerLink="/ahorros" class="boton boton-icono" aria-label="Volver a ahorros">‹</a>
        <h1 class="titulo">{{ objetivo()?.nombre }}</h1>
      </header>

      @if (objetivo(); as o) {
        <section class="destacado">
          <span class="etiqueta">Apartado para este objetivo @if (o.fecha_meta) { · para {{ o.fecha_meta }} }</span>
          <span class="num monto-grande">{{ o.apartado | monto: 'simple' : o.moneda }}</span>
          <bi-barra-progreso [actual]="o.apartado" [meta]="o.monto_meta" [sobreOscuro]="true" etiqueta="Progreso del objetivo" />
          <div class="datos">
            <div><span class="etiqueta">Meta</span><span class="num">{{ o.monto_meta | monto: 'simple' : o.moneda }}</span></div>
            <div><span class="etiqueta">Falta</span><span class="num">{{ falta() | monto: 'simple' : o.moneda }}</span></div>
          </div>
        </section>

        <form class="tarjeta formulario" (ngSubmit)="aplicar()">
          <div class="segmentado" role="group" aria-label="Movimiento">
            <button type="button" [attr.aria-pressed]="modo() === 'apartar'" (click)="modo.set('apartar')">Apartar</button>
            <button type="button" [attr.aria-pressed]="modo() === 'devolver'" (click)="modo.set('devolver')">
              Devolver a {{ o.moneda === 'USD' ? 'dólares' : 'ahorros' }}
            </button>
          </div>
          <span class="atenuado chico">
            @if (modo() === 'apartar') { Sale de {{ nombreLibre() }}: <span class="num">{{ libre() | monto: 'simple' : o.moneda }}</span> }
            @else { Vuelve a {{ nombreLibre() }}. Apartado: <span class="num">{{ o.apartado | monto: 'simple' : o.moneda }}</span> }
          </span>
          <label class="campo">Monto · {{ o.moneda }}
            <input id="objetivo-monto" name="monto" inputmode="decimal" placeholder="0" class="num" [(ngModel)]="montoTexto" />
          </label>
          @if (error()) { <p class="error" role="alert">{{ error() }}</p> }
          <button type="submit" class="boton boton-primario" [disabled]="guardando()">
            {{ modo() === 'apartar' ? 'Apartar' : 'Devolver' }}
          </button>
        </form>

        <section class="seccion" aria-labelledby="historial-titulo">
          <h2 id="historial-titulo">Historial</h2>
          @if (historial().length) {
            <ul class="lista">
              @for (h of historial(); track h.id) {
                <li class="movimiento">
                  <span class="pila"><span class="nombre">{{ h.titulo }}</span><span class="atenuado chico">{{ h.detalle }}</span></span>
                  <span class="num" [class.ingreso]="h.monto > 0" [class.gasto]="h.monto < 0">{{ h.monto | monto: 'signo' : o.moneda }}</span>
                </li>
              }
            </ul>
          } @else if (!movimientosCargados()) {
            <p class="vacio" aria-busy="true">Cargando…</p>
          } @else {
            <p class="vacio">Todavía no apartaste {{ o.moneda === 'USD' ? 'dólares' : 'plata' }} para este objetivo.</p>
          }
        </section>

        <button type="button" class="boton" (click)="archivar()">Archivar objetivo</button>
      } @else if (error()) {
        <p class="error" role="alert">{{ error() }}</p>
      }
    </main>
  `,
  styles: `
    .titulo { font-size: 20px; flex: 1; }
    .datos { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
    .datos div, .pila { display: flex; flex-direction: column; gap: 2px; }
    .formulario { display: flex; flex-direction: column; gap: 12px; }
    .chico { font-size: 13px; }
    .movimiento { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 10px 0; }
    .nombre { font-weight: 500; }
  `,
})
export class ObjetivoPagina implements OnInit {
  private readonly api = inject(ApiServicio);
  private readonly router = inject(Router);

  /** Id del objetivo, desde la ruta /ahorros/:id */
  readonly id = input.required<string>();

  readonly resumen = signal<Resumen | null>(null);
  readonly movimientos = signal<Movimiento[]>([]);
  /** Hasta la primera respuesta no se dice que no hay movimientos. */
  readonly movimientosCargados = signal(false);
  readonly modo = signal<Modo>('apartar');
  readonly error = signal<string | null>(null);
  readonly guardando = signal(false);
  montoTexto = '';

  readonly objetivo = computed<Objetivo | undefined>(() => this.resumen()?.objetivos.find((o) => o.id === this.id()));
  /** Los objetivos en dólares se apartan desde los dólares; los de pesos, desde los ahorros. */
  readonly bolsillo = computed(() => (this.objetivo()?.moneda === 'USD' ? ('dolares' as const) : ('ahorros' as const)));
  readonly nombreLibre = computed(() => (this.bolsillo() === 'dolares' ? 'tus dólares libres' : 'tu ahorro libre'));
  readonly libre = computed(() => {
    const saldos = this.resumen()?.saldos;
    if (!saldos) return null;
    return this.bolsillo() === 'dolares' ? saldos.dolares_libres : saldos.ahorro_libre;
  });
  readonly falta = computed(() => {
    const o = this.objetivo();
    return o ? Math.max(0, Number(o.monto_meta) - Number(o.apartado)) : 0;
  });

  readonly historial = computed(() =>
    this.movimientos()
      .map((m) => {
        const parte = m.partes.find((p) => p.objetivo_id === this.id());
        if (!parte) return null;
        const monto = Number(parte.monto);
        const devuelto = this.bolsillo() === 'dolares' ? 'Devuelto a dólares libres' : 'Devuelto a ahorros';
        const titulo = m.tipo === 'gasto' ? (m.descripcion ?? 'Gasto') : monto > 0 ? 'Apartado' : devuelto;
        const detalle = `${nombreDia(new Date(m.ocurrido_en))}${m.tipo === 'gasto' ? ' · Gasto pagado con este objetivo' : ''}`;
        return { id: m.id, titulo, detalle, monto };
      })
      .filter((h) => h !== null),
  );

  ngOnInit(): void {
    this.cargar();
  }

  aplicar(): void {
    const monto = montoDesdeTexto(this.montoTexto);
    if (!monto) {
      this.error.set('Escribí un monto mayor a cero, con hasta dos decimales.');
      return;
    }
    const objetivo = { bolsillo: this.bolsillo(), objetivo_id: this.id() };
    const libre = { bolsillo: this.bolsillo() };
    const apartar = this.modo() === 'apartar';
    this.guardando.set(true);
    this.error.set(null);
    this.api
      .transferir({
        monto,
        ocurrido_en: fechaParaApi(hoyLocal()),
        desde: apartar ? libre : objetivo,
        hacia: apartar ? objetivo : libre,
      })
      .subscribe({
        next: () => {
          this.guardando.set(false);
          this.montoTexto = '';
          this.cargar();
        },
        error: (error) => {
          this.guardando.set(false);
          this.error.set(mensajeDeError(error));
        },
      });
  }

  archivar(): void {
    this.api.actualizarObjetivo(this.id(), { archivado: true }).subscribe({
      next: () => this.router.navigateByUrl('/ahorros'),
      error: (error) => this.error.set(mensajeDeError(error)),
    });
  }

  private cargar(): void {
    this.api.resumen(claveMes()).subscribe({
      next: (resumen) => {
        this.resumen.set(resumen);
        if (!resumen.objetivos.some((o) => o.id === this.id())) this.error.set('El objetivo no existe o está archivado.');
      },
      error: (error) => this.error.set(mensajeDeError(error)),
    });
    this.api.movimientos().subscribe((movimientos) => {
      this.movimientos.set(movimientos);
      this.movimientosCargados.set(true);
    });
  }
}
