import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { MontoPipe } from '../../compartido/monto.pipe';
import { BarraProgresoComponent } from '../../compartido/ui/barra-progreso.component';
import { FilaMovimientoComponent } from '../../compartido/ui/fila-movimiento.component';
import { NavegacionComponent } from '../../compartido/ui/navegacion.component';
import { ApiServicio, mensajeDeError } from '../../nucleo/api.servicio';
import { CatalogoStore } from '../../nucleo/catalogo.store';
import { claveMes, moverMes, nombreMes } from '../../nucleo/formato';
import { Movimiento, Resumen } from '../../nucleo/modelos';

/** Inicio: tu plata, el balance del mes, los objetivos y los últimos movimientos. */
@Component({
  selector: 'bi-inicio',
  imports: [RouterLink, MontoPipe, BarraProgresoComponent, FilaMovimientoComponent, NavegacionComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <main class="pantalla">
      <header class="encabezado">
        <div class="saludo">
          <span class="atenuado">{{ saludo() }},</span>
          <h1>{{ nombre() }}</h1>
        </div>
        <div class="mes">
          <button type="button" class="boton boton-icono" (click)="cambiarMes(-1)" aria-label="Mes anterior">‹</button>
          <span>{{ nombreMes(mes()) }}</span>
          <button type="button" class="boton boton-icono" (click)="cambiarMes(1)" aria-label="Mes siguiente">›</button>
        </div>
      </header>

      @if (error()) { <p class="error" role="alert">{{ error() }}</p> }

      @if (resumen(); as r) {
        <section class="destacado" aria-label="Tu plata">
          <div class="pila">
            <span class="etiqueta">Tu plata · ARS</span>
            <span class="num monto-grande">{{ r.saldos.total | monto }}</span>
            <span class="etiqueta desglose">
              <span>Para gastar <span class="num claro">{{ r.saldos.disponible | monto }}</span></span>
              <span>Ahorrado <span class="num lima">{{ r.saldos.ahorros | monto }}</span></span>
            </span>
          </div>
          <div class="totales">
            <div class="total">
              <span class="etiqueta">Ingresos del mes</span>
              <span class="num ingreso-claro">{{ r.ingresos_mes | monto }}</span>
            </div>
            <div class="total">
              <span class="etiqueta">Gastos del mes</span>
              <span class="num gasto-claro">{{ r.gastos_mes | monto }}</span>
            </div>
          </div>
        </section>

        <section class="seccion" aria-labelledby="ahorros-titulo">
          <div class="seccion-titulo">
            <div class="pila">
              <h2 id="ahorros-titulo">Ahorros</h2>
              <span class="atenuado chico">Ahorrado <span class="num">{{ r.saldos.ahorros | monto }}</span> · libre <span class="num">{{ r.saldos.ahorro_libre | monto }}</span></span>
            </div>
            <a routerLink="/ahorros" aria-label="Ver todos los ahorros">Ver todo</a>
          </div>
          @if (r.objetivos.length) {
            <div class="objetivos">
              @for (objetivo of r.objetivos; track objetivo.id) {
                <a class="tarjeta objetivo" [routerLink]="['/ahorros', objetivo.id]">
                  <span class="nombre">{{ objetivo.nombre }}</span>
                  <span class="num atenuado chico">{{ objetivo.apartado | monto }} / {{ objetivo.monto_meta | monto }}</span>
                  <bi-barra-progreso [actual]="objetivo.apartado" [meta]="objetivo.monto_meta" [etiqueta]="'Progreso de ' + objetivo.nombre" />
                </a>
              }
            </div>
          } @else {
            <a class="tarjeta vacio-enlace" routerLink="/ahorros">Creá tu primer objetivo de ahorro</a>
          }
        </section>
      }

      <section class="seccion" aria-labelledby="ultimos-titulo">
        <div class="seccion-titulo">
          <h2 id="ultimos-titulo">Últimos movimientos</h2>
          <a routerLink="/movimientos" aria-label="Ver todos los movimientos">Ver todos</a>
        </div>
        @if (ultimos().length) {
          <ul class="lista">
            @for (m of ultimos(); track m.id) {
              <li><bi-fila-movimiento [movimiento]="m" [nombreCategoria]="catalogo.nombresCategoria().get(m.categoria_id ?? '') ?? null"
                [nombreMetodo]="catalogo.nombresMetodo().get(m.metodo_pago_id ?? '') ?? null" /></li>
            }
          </ul>
        } @else {
          <p class="vacio">Todavía no cargaste movimientos este mes. Tocá + para agregar el primero.</p>
        }
      </section>
    </main>
    <bi-navegacion />
  `,
  styles: `
    .saludo, .pila { display: flex; flex-direction: column; gap: 4px; }
    .mes { display: flex; align-items: center; gap: 4px; font-size: 14px; font-weight: 500; }
    .desglose { display: flex; flex-wrap: wrap; gap: 12px; }
    .claro { color: var(--sobre-bosque); }
    .lima { color: var(--lima); }
    .totales { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
    .total { background: var(--bosque-2); border-radius: 16px; padding: 12px 14px; display: flex; flex-direction: column; gap: 4px; }
    .ingreso-claro { color: var(--ingreso-claro); }
    .gasto-claro { color: var(--gasto-claro); }
    .chico { font-size: 13px; }
    .seccion-titulo a { font-size: 14px; font-weight: 500; min-height: 44px; display: flex; align-items: center; }
    .objetivos { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 12px; }
    .objetivo { display: flex; flex-direction: column; gap: 10px; text-decoration: none; color: var(--tinta); }
    .nombre { font-size: 14px; font-weight: 600; }
    .vacio-enlace { text-align: center; color: var(--atenuado); }
  `,
})
export class InicioPagina implements OnInit {
  private readonly api = inject(ApiServicio);
  readonly catalogo = inject(CatalogoStore);

  readonly mes = signal(claveMes());
  readonly resumen = signal<Resumen | null>(null);
  readonly ultimos = signal<Movimiento[]>([]);
  readonly nombre = signal('');
  readonly error = signal<string | null>(null);
  readonly nombreMes = nombreMes;

  ngOnInit(): void {
    this.catalogo.cargar();
    this.api.perfil().subscribe((perfil) => this.nombre.set(perfil.nombre_visible));
    this.cargar();
  }

  saludo(): string {
    const hora = new Date().getHours();
    if (hora < 12) return 'Buen día';
    if (hora < 20) return 'Buenas tardes';
    return 'Buenas noches';
  }

  cambiarMes(delta: number): void {
    this.mes.update((mes) => moverMes(mes, delta));
    this.cargar();
  }

  private cargar(): void {
    this.error.set(null);
    this.api.resumen(this.mes()).subscribe({
      next: (resumen) => this.resumen.set(resumen),
      error: (error) => this.error.set(mensajeDeError(error)),
    });
    this.api.movimientos({ mes: this.mes() }).subscribe({
      next: (movimientos) => this.ultimos.set(movimientos.slice(0, 5)),
      error: (error) => this.error.set(mensajeDeError(error)),
    });
  }
}
