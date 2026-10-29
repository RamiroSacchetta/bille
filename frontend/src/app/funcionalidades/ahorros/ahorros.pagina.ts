import { ChangeDetectionStrategy, Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { Observable } from 'rxjs';

import { MontoPipe } from '../../compartido/monto.pipe';
import { BarraProgresoComponent } from '../../compartido/ui/barra-progreso.component';
import { NavegacionComponent } from '../../compartido/ui/navegacion.component';
import { ApiServicio, mensajeDeError } from '../../nucleo/api.servicio';
import { claveMes, fechaParaApi, hoyLocal, montoDesdeTexto, nombreDia } from '../../nucleo/formato';
import { Moneda, Movimiento, Resumen } from '../../nucleo/modelos';

type Accion = 'mandar' | 'pasar' | 'objetivo' | null;

interface MovimientoAhorro {
  id: string;
  titulo: string;
  detalle: string;
  monto: number;
}

/** Ahorros: el total ahorrado, cómo se reparte entre ahorro libre y objetivos, y sus movimientos. */
@Component({
  selector: 'bi-ahorros',
  imports: [FormsModule, RouterLink, MontoPipe, BarraProgresoComponent, NavegacionComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <main class="pantalla">
      <header class="encabezado">
        <h1>Ahorros</h1>
        <button type="button" class="boton" (click)="abrir('objetivo')">+ Nuevo objetivo</button>
      </header>

      @if (resumen(); as r) {
        <section class="destacado" aria-label="Total ahorrado">
          <div class="pila">
            <span class="etiqueta">Ahorrado · ARS</span>
            <span class="num monto-grande">{{ r.saldos.ahorros | monto }}</span>
          </div>
          @if (reparto().length) {
            <span class="reparto" role="img" [attr.aria-label]="descripcionReparto()">
              @for (tramo of reparto(); track tramo.nombre) {
                <span [style.width.%]="tramo.porcentaje" [style.background]="tramo.color"></span>
              }
            </span>
            <ul class="leyenda">
              @for (tramo of reparto(); track tramo.nombre) {
                <li><span class="punto" [style.background]="tramo.color" aria-hidden="true"></span>
                  <span class="nombre">{{ tramo.nombre }}</span><span class="num">{{ tramo.monto | monto }}</span></li>
              }
            </ul>
          }
        </section>
      }

      @if (resumen(); as r) {
        <section class="tarjeta dolares" aria-labelledby="dolares-titulo">
          <div class="pila">
            <h2 id="dolares-titulo">Dólares</h2>
            <span class="atenuado chico">Aparte de los pesos, sin cotización.</span>
          </div>
          <div class="pila derecha">
            <span class="num total-dolares">{{ r.saldos.dolares | monto: 'simple' : 'USD' }}</span>
            <span class="atenuado chico">libres <span class="num">{{ r.saldos.dolares_libres | monto: 'simple' : 'USD' }}</span></span>
          </div>
        </section>
      }

      <div class="acciones">
        <button type="button" class="boton boton-primario" (click)="abrir('mandar')">Mandar a ahorros</button>
        <button type="button" class="boton" (click)="abrir('pasar')">Pasar a disponible</button>
      </div>

      @if (accion()) {
        <form class="tarjeta formulario" (ngSubmit)="confirmar()">
          <h2>{{ tituloAccion() }}</h2>
          @if (accion() === 'objetivo') {
            <label class="campo">Nombre
              <input id="objetivo-nombre" name="nombre" maxlength="80" placeholder="Ej: Viaje a Bariloche" [(ngModel)]="nombreObjetivo" />
            </label>
            <div class="segmentado" role="group" aria-label="Moneda del objetivo">
              <button type="button" [attr.aria-pressed]="monedaObjetivo() === 'ARS'" (click)="monedaObjetivo.set('ARS')">Pesos</button>
              <button type="button" [attr.aria-pressed]="monedaObjetivo() === 'USD'" (click)="monedaObjetivo.set('USD')">Dólares</button>
            </div>
            <label class="campo">Fecha meta (opcional)
              <input id="objetivo-fecha" name="fecha" type="date" [(ngModel)]="fechaObjetivo" />
            </label>
          }
          <label class="campo">{{ accion() === 'objetivo' ? 'Meta · ' + monedaObjetivo() : 'Monto' }}
            <input id="ahorros-monto" name="monto" inputmode="decimal" placeholder="0" class="num" [(ngModel)]="montoTexto" />
          </label>
          @if (error()) { <p class="error" role="alert">{{ error() }}</p> }
          <div class="acciones">
            <button type="button" class="boton" (click)="abrir(null)">Cancelar</button>
            <button type="submit" class="boton boton-primario" [disabled]="guardando()">Confirmar</button>
          </div>
        </form>
      }

      <section class="seccion" aria-labelledby="objetivos-titulo">
        <h2 id="objetivos-titulo">Objetivos</h2>
        @for (objetivo of resumen()?.objetivos ?? []; track objetivo.id) {
          <a class="tarjeta objetivo" [routerLink]="['/ahorros', objetivo.id]">
            <span class="fila"><span class="nombre">{{ objetivo.nombre }}</span>
              <span class="num">{{ porcentaje(objetivo.apartado, objetivo.monto_meta) }}%</span></span>
            <bi-barra-progreso [actual]="objetivo.apartado" [meta]="objetivo.monto_meta" [etiqueta]="'Progreso de ' + objetivo.nombre" />
            <span class="fila atenuado chico"><span class="num">{{ objetivo.apartado | monto: 'simple' : objetivo.moneda }} / {{ objetivo.monto_meta | monto: 'simple' : objetivo.moneda }}</span>
              @if (objetivo.fecha_meta) { <span>Para {{ objetivo.fecha_meta }}</span> }</span>
          </a>
        } @empty {
          <p class="vacio">Todavía no tenés objetivos. Creá uno para apartar plata de tus ahorros o de tus dólares, por ejemplo para un viaje.</p>
        }
      </section>

      <section class="seccion" aria-labelledby="movimientos-ahorro-titulo">
        <h2 id="movimientos-ahorro-titulo">Últimos movimientos de ahorros</h2>
        @if (movimientosAhorro().length) {
          <ul class="lista">
            @for (m of movimientosAhorro(); track m.id) {
              <li class="movimiento">
                <span class="pila"><span class="titulo">{{ m.titulo }}</span><span class="atenuado chico">{{ m.detalle }}</span></span>
                <span class="num" [class.ingreso]="m.monto > 0" [class.gasto]="m.monto < 0">{{ m.monto | monto: 'signo' }}</span>
              </li>
            }
          </ul>
        } @else {
          <p class="vacio">Cuando mandes plata a ahorros, va a aparecer acá.</p>
        }
      </section>
    </main>
    <bi-navegacion />
  `,
  styles: `
    .pila { display: flex; flex-direction: column; gap: 4px; }
    .reparto { display: flex; gap: 2px; height: 12px; border-radius: 6px; overflow: hidden; }
    .leyenda { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; font-size: 13px; }
    .leyenda li { display: flex; align-items: center; gap: 8px; }
    .punto { width: 10px; height: 10px; border-radius: 5px; }
    .leyenda .nombre { flex: 1; }
    .acciones { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
    .formulario { display: flex; flex-direction: column; gap: 12px; }
    .objetivo { display: flex; flex-direction: column; gap: 10px; text-decoration: none; color: var(--tinta); }
    .fila { display: flex; justify-content: space-between; gap: 8px; }
    .nombre { font-weight: 600; }
    .chico { font-size: 13px; }
    .movimiento { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 10px 0; }
    .titulo { font-weight: 500; }
    .dolares { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
    .derecha { align-items: flex-end; }
    .total-dolares { font-size: 20px; font-weight: 600; }
  `,
})
export class AhorrosPagina implements OnInit {
  private readonly api = inject(ApiServicio);

  readonly resumen = signal<Resumen | null>(null);
  readonly movimientos = signal<Movimiento[]>([]);
  readonly accion = signal<Accion>(null);
  readonly error = signal<string | null>(null);
  readonly guardando = signal(false);
  readonly monedaObjetivo = signal<Moneda>('ARS');

  montoTexto = '';
  nombreObjetivo = '';
  fechaObjetivo = '';

  readonly reparto = computed(() => {
    const r = this.resumen();
    if (!r || Number(r.saldos.ahorros) <= 0) return [];
    const total = Number(r.saldos.ahorros);
    const colores = ['#F5F5F0', '#6E8A7C', '#9FD3FF', '#FFB98A'];
    const tramos = [
      { nombre: 'Ahorro libre', monto: Number(r.saldos.ahorro_libre), color: 'var(--lima)' },
      // Los ahorros son en pesos: los objetivos en dólares no entran en este reparto
      ...r.objetivos.filter((o) => o.moneda === 'ARS').map((o, i) => ({ nombre: o.nombre, monto: Number(o.apartado), color: colores[i % colores.length] })),
    ].filter((t) => t.monto > 0);
    return tramos.map((t) => ({ ...t, porcentaje: (t.monto / total) * 100 }));
  });

  readonly movimientosAhorro = computed<MovimientoAhorro[]>(() =>
    this.movimientos()
      .map((m) => {
        // Solo la parte del movimiento que tocó el bolsillo de ahorros (sin contar apartados internos)
        const partesAhorro = m.partes.filter((p) => p.bolsillo === 'ahorros');
        const neto = partesAhorro.reduce((suma, p) => suma + Number(p.monto), 0);
        if (!partesAhorro.length || (m.tipo === 'transferencia' && neto === 0)) return null;
        const titulo = m.descripcion ?? tituloAhorro(m, neto);
        return { id: m.id, titulo, detalle: nombreDia(new Date(m.ocurrido_en)), monto: neto };
      })
      .filter((m): m is MovimientoAhorro => m !== null)
      .slice(0, 10),
  );

  readonly descripcionReparto = computed(() =>
    this.reparto()
      .map((t) => `${t.nombre} ${Math.round(t.porcentaje)}%`)
      .join(', '),
  );

  ngOnInit(): void {
    this.cargar();
  }

  porcentaje(actual: string, meta: string): number {
    return Math.min(100, Math.round((Number(actual) / Number(meta)) * 100));
  }

  tituloAccion(): string {
    return { mandar: 'Mandar a ahorros', pasar: 'Pasar a disponible', objetivo: 'Nuevo objetivo' }[this.accion() ?? 'mandar'];
  }

  abrir(accion: Accion): void {
    this.accion.set(accion);
    this.error.set(null);
    this.montoTexto = '';
    this.nombreObjetivo = '';
    this.fechaObjetivo = '';
    this.monedaObjetivo.set('ARS');
  }

  confirmar(): void {
    const monto = montoDesdeTexto(this.montoTexto);
    if (!monto) {
      this.error.set('Escribí un monto mayor a cero, con hasta dos decimales.');
      return;
    }
    const accion = this.accion();
    if (accion === 'objetivo' && !this.nombreObjetivo.trim()) {
      this.error.set('Ponele un nombre al objetivo.');
      return;
    }
    const pedido: Observable<unknown> =
      accion === 'objetivo'
        ? this.api.crearObjetivo({
            nombre: this.nombreObjetivo.trim(),
            monto_meta: monto,
            fecha_meta: this.fechaObjetivo || null,
            moneda: this.monedaObjetivo(),
          })
        : this.api.transferir({
            monto,
            ocurrido_en: fechaParaApi(hoyLocal()),
            desde: { bolsillo: accion === 'mandar' ? 'disponible' : 'ahorros' },
            hacia: { bolsillo: accion === 'mandar' ? 'ahorros' : 'disponible' },
          });
    this.guardando.set(true);
    pedido.subscribe({
      next: () => {
        this.guardando.set(false);
        this.abrir(null);
        this.cargar();
      },
      error: (error) => {
        this.guardando.set(false);
        this.error.set(mensajeDeError(error));
      },
    });
  }

  private cargar(): void {
    this.api.resumen(claveMes()).subscribe((resumen) => this.resumen.set(resumen));
    this.api.movimientos().subscribe((movimientos) => this.movimientos.set(movimientos));
  }
}

function tituloAhorro(m: Movimiento, neto: number): string {
  if (m.tipo === 'gasto') return 'Gasto con ahorros';
  if (m.tipo === 'cambio') return neto < 0 ? 'Compraste dólares' : 'Vendiste dólares';
  return neto > 0 ? 'Mandaste a ahorros' : 'Pasaste a disponible';
}
