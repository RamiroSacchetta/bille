import { ChangeDetectionStrategy, Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { Observable } from 'rxjs';

import { MontoPipe } from '../../compartido/monto.pipe';
import { ApiServicio, mensajeDeError } from '../../nucleo/api.servicio';
import { CatalogoStore } from '../../nucleo/catalogo.store';
import { claveMes, fechaParaApi, hoyLocal, montoDesdeTexto } from '../../nucleo/formato';
import { Movimiento, Resumen } from '../../nucleo/modelos';
import { Origen, estadoDivision, origenesParaApi } from './division';

type Tipo = 'gasto' | 'ingreso';

/** Carga rápida de un gasto o un ingreso, con opción de dividir el pago entre plata del mes y ahorros. */
@Component({
  selector: 'bi-carga',
  imports: [FormsModule, RouterLink, MontoPipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <main class="pantalla">
      <header class="encabezado">
        <a routerLink="/" class="boton boton-icono" aria-label="Cerrar">✕</a>
        <div class="segmentado" role="group" aria-label="Tipo de movimiento">
          <button type="button" [attr.aria-pressed]="tipo() === 'gasto'" (click)="cambiarTipo('gasto')">Gasto</button>
          <button type="button" [attr.aria-pressed]="tipo() === 'ingreso'" (click)="cambiarTipo('ingreso')">Ingreso</button>
        </div>
        <span class="espacio"></span>
      </header>

      <form class="formulario" (ngSubmit)="guardar()">
        <label class="monto">
          <span class="atenuado">Monto · ARS</span>
          <input id="carga-monto" name="monto" inputmode="decimal" autocomplete="off" placeholder="0"
            [ngModel]="montoTexto()" (ngModelChange)="montoTexto.set($event)" [class]="tipo()" />
        </label>

        <fieldset>
          <legend>Categoría</legend>
          <div class="chips">
            @for (categoria of categorias(); track categoria.id) {
              <button type="button" class="chip" [attr.aria-pressed]="categoriaId() === categoria.id" (click)="categoriaId.set(categoria.id)">
                {{ categoria.nombre }}
              </button>
            }
          </div>
        </fieldset>

        <fieldset>
          <legend>{{ tipo() === 'gasto' ? 'Pagado con' : 'Cobrado en' }}</legend>
          <div class="chips">
            @for (metodo of metodos(); track metodo.id) {
              <button type="button" class="chip" [attr.aria-pressed]="metodoId() === metodo.id" (click)="metodoId.set(metodo.id)">
                {{ metodo.nombre }}
              </button>
            }
          </div>
        </fieldset>

        <div class="fila">
          <label class="campo">Fecha
            <input id="carga-fecha" name="fecha" type="date" [ngModel]="fecha()" (ngModelChange)="fecha.set($event)" />
          </label>
          <label class="campo nota">Nota
            <input id="carga-nota" name="nota" maxlength="200" placeholder="Ej: arreglo del auto" [ngModel]="nota()" (ngModelChange)="nota.set($event)" />
          </label>
        </div>

        @if (tipo() === 'ingreso') {
          <fieldset>
            <legend>Va a</legend>
            <div class="segmentado" role="group" aria-label="Destino del ingreso">
              <button type="button" [attr.aria-pressed]="destino() === 'disponible'" (click)="destino.set('disponible')">Plata del mes</button>
              <button type="button" [attr.aria-pressed]="destino() === 'ahorros'" (click)="destino.set('ahorros')">Ahorros</button>
            </div>
          </fieldset>
        } @else {
          <fieldset>
            <legend>Sale de</legend>
            @if (!dividir()) {
              <button type="button" class="boton sale-de" (click)="activarDivision()" aria-label="Sale de la plata del mes. Dividir el pago">
                <span>Plata del mes</span><span>Dividir ›</span>
              </button>
            } @else {
              <ul class="lista division">
                @for (origen of origenes(); track origen.clave) {
                  <li>
                    <label [for]="'origen-' + origen.clave">
                      <span>{{ origen.nombre }}</span>
                      <span class="atenuado chico">Tenés <span class="num">{{ origen.saldo | monto }}</span></span>
                    </label>
                    <input [id]="'origen-' + origen.clave" [name]="'origen-' + origen.clave" inputmode="decimal" placeholder="0"
                      class="num" [ngModel]="textoOrigen(origen.clave)" (ngModelChange)="cambiarOrigen(origen.clave, $event)" />
                  </li>
                }
              </ul>
              <p class="estado" [class.cuadra]="division().cuadra" role="status">{{ division().mensaje }}</p>
              <button type="button" class="boton" (click)="dividir.set(false)">Pagar todo con la plata del mes</button>
            }
          </fieldset>
        }

        @if (error()) { <p class="error" role="alert">{{ error() }}</p> }

        <button type="submit" class="boton boton-primario boton-ancho" [disabled]="guardando()">
          Guardar {{ tipo() }}
        </button>
      </form>
    </main>
  `,
  styles: `
    .espacio { width: 44px; }
    .formulario { display: flex; flex-direction: column; gap: 18px; }
    .monto { display: flex; flex-direction: column; align-items: center; gap: 4px; font-size: 13px; }
    .monto input {
      width: 100%; border: 0; background: transparent; text-align: center;
      font-family: var(--fuente-numeros); font-size: 44px; letter-spacing: -0.02em;
    }
    .monto input.gasto { color: var(--gasto); }
    .monto input.ingreso { color: var(--ingreso); }
    fieldset { border: 0; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 8px; }
    legend { font-size: 13px; font-weight: 600; color: var(--atenuado); margin-bottom: 8px; padding: 0; }
    .fila { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 2fr); gap: 8px; }
    .sale-de { justify-content: space-between; width: 100%; }
    .division li { display: flex; align-items: center; gap: 12px; padding: 10px 0; }
    .division label { flex: 1; display: flex; flex-direction: column; gap: 2px; }
    .division input { width: 120px; min-height: 44px; border: 1px solid var(--linea); border-radius: 12px; padding: 0 10px; text-align: right; font-size: 15px; }
    .chico { font-size: 12px; }
    .estado { margin: 0; text-align: center; font-weight: 600; color: var(--gasto); }
    .estado.cuadra { color: var(--ingreso); }
  `,
})
export class CargaPagina implements OnInit {
  private readonly api = inject(ApiServicio);
  private readonly router = inject(Router);
  private readonly catalogo = inject(CatalogoStore);

  readonly tipo = signal<Tipo>('gasto');
  readonly montoTexto = signal('');
  readonly categoriaId = signal<string | null>(null);
  readonly metodoId = signal<string | null>(null);
  readonly fecha = signal(hoyLocal());
  readonly nota = signal('');
  readonly destino = signal<'disponible' | 'ahorros'>('disponible');
  readonly dividir = signal(false);
  readonly montosOrigen = signal<Record<string, number>>({});
  readonly resumen = signal<Resumen | null>(null);
  readonly error = signal<string | null>(null);
  readonly guardando = signal(false);

  readonly categorias = computed(() => this.catalogo.categorias().filter((c) => c.tipo === this.tipo()));
  readonly metodos = computed(() => this.catalogo.metodos().filter((m) => m.activo));
  readonly monto = computed(() => Number(montoDesdeTexto(this.montoTexto()) ?? 0));

  readonly origenes = computed<Origen[]>(() => {
    const resumen = this.resumen();
    if (!resumen) return [];
    return [
      { clave: 'mes', nombre: 'Plata del mes', bolsillo: 'disponible', objetivo_id: null, saldo: Number(resumen.saldos.disponible) },
      { clave: 'libre', nombre: 'Ahorro libre', bolsillo: 'ahorros', objetivo_id: null, saldo: Number(resumen.saldos.ahorro_libre) },
      ...resumen.objetivos.map((o) => ({
        clave: o.id,
        nombre: o.nombre,
        bolsillo: 'ahorros' as const,
        objetivo_id: o.id,
        saldo: Number(o.apartado),
      })),
    ];
  });

  readonly division = computed(() => estadoDivision(this.monto(), this.montosOrigen()));

  ngOnInit(): void {
    this.catalogo.cargar();
    this.api.resumen(claveMes()).subscribe((resumen) => this.resumen.set(resumen));
  }

  cambiarTipo(tipo: Tipo): void {
    this.tipo.set(tipo);
    this.categoriaId.set(null);
    this.dividir.set(false);
  }

  activarDivision(): void {
    // Arranca con todo en la plata del mes y el usuario reparte desde ahí
    this.montosOrigen.set({ mes: this.monto() });
    this.dividir.set(true);
  }

  textoOrigen(clave: string): string {
    const monto = this.montosOrigen()[clave];
    return monto ? String(monto) : '';
  }

  cambiarOrigen(clave: string, texto: string): void {
    const monto = Number(montoDesdeTexto(texto) ?? 0);
    this.montosOrigen.update((montos) => ({ ...montos, [clave]: monto }));
  }

  guardar(): void {
    const monto = montoDesdeTexto(this.montoTexto());
    if (!monto) {
      this.error.set('Escribí un monto mayor a cero, con hasta dos decimales.');
      return;
    }
    if (this.tipo() === 'gasto' && this.dividir() && !this.division().cuadra) {
      this.error.set(this.division().mensaje);
      return;
    }
    const base = {
      monto,
      ocurrido_en: fechaParaApi(this.fecha()),
      descripcion: this.nota().trim() || null,
      categoria_id: this.categoriaId(),
      metodo_pago_id: this.metodoId(),
    };
    const pedido: Observable<Movimiento> =
      this.tipo() === 'gasto'
        ? this.api.registrarGasto({
            ...base,
            origenes: this.dividir() ? origenesParaApi(this.origenes(), this.montosOrigen()) : null,
          })
        : this.api.registrarIngreso({ ...base, destino: { bolsillo: this.destino() } });

    this.guardando.set(true);
    this.error.set(null);
    pedido.subscribe({
      next: () => this.router.navigateByUrl('/'),
      error: (error) => {
        this.guardando.set(false);
        this.error.set(mensajeDeError(error));
      },
    });
  }
}
