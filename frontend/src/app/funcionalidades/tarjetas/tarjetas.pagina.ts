import { ChangeDetectionStrategy, Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { MontoPipe } from '../../compartido/monto.pipe';
import { NavegacionComponent } from '../../compartido/ui/navegacion.component';
import { ApiServicio, mensajeDeError } from '../../nucleo/api.servicio';
import { CatalogoStore } from '../../nucleo/catalogo.store';
import { claveMes, fechaParaApi, hoyLocal, montoDesdeTexto } from '../../nucleo/formato';
import { CompraTarjeta, Resumen, Tarjeta } from '../../nucleo/modelos';
import { cuotaActual, mesCorto } from './cuotas';

/**
 * Tarjetas de crédito: deuda estimada, resúmenes, compras en cuotas y pago del resumen.
 * Lo anotado es aproximado; el pago real es lo que descuenta de tu plata.
 */
@Component({
  selector: 'bi-tarjetas',
  imports: [FormsModule, RouterLink, MontoPipe, NavegacionComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <main class="pantalla">
      <header class="encabezado">
        <h1>Tarjetas</h1>
        <button type="button" class="boton" (click)="mostrarNueva.set(!mostrarNueva())">+ Nueva tarjeta</button>
      </header>

      @if (mostrarNueva()) {
        <form class="tarjeta formulario" (ngSubmit)="crearTarjeta()">
          <h2>Nueva tarjeta</h2>
          <label class="campo">Nombre
            <input id="tarjeta-nombre" name="nombre" maxlength="60" placeholder="Ej: Visa Galicia" [(ngModel)]="nombreNueva" />
          </label>
          <div class="dos">
            <label class="campo">Día de cierre
              <input id="tarjeta-cierre" name="cierre" type="number" min="1" max="31" [(ngModel)]="cierreNueva" />
            </label>
            <label class="campo">Día de vencimiento
              <input id="tarjeta-vencimiento" name="vencimiento" type="number" min="1" max="31" [(ngModel)]="vencimientoNueva" />
            </label>
          </div>
          <button type="submit" class="boton boton-primario">Guardar tarjeta</button>
        </form>
      }

      @if (error()) { <p class="error" role="alert">{{ error() }}</p> }

      @if (tarjetas().length > 1) {
        <div class="chips" role="group" aria-label="Elegir tarjeta">
          @for (t of tarjetas(); track t.id) {
            <button type="button" class="chip" [attr.aria-pressed]="t.id === elegida()?.id" (click)="elegir(t.id)">{{ t.nombre }}</button>
          }
        </div>
      }

      @if (elegida(); as t) {
        <section class="destacado" [attr.aria-label]="'Tarjeta ' + t.nombre">
          <div class="pila">
            <span class="etiqueta">{{ t.nombre }} · debés aprox.</span>
            <span class="num monto-grande">{{ t.deuda_estimada | monto }}</span>
            <span class="etiqueta">Estimado con lo que anotaste. El dato real es lo que pagás.</span>
          </div>
          <div class="resumenes">
            <div class="bloque">
              <span class="etiqueta">Último resumen cerrado</span>
              <span class="num">{{ t.resumen_cerrado | monto }}</span>
            </div>
            <div class="bloque">
              <span class="etiqueta">En curso · cierra el {{ t.dia_cierre }}</span>
              <span class="num">{{ t.resumen_en_curso | monto }}</span>
            </div>
          </div>
          @if (t.proximos.length) {
            <ul class="proximos">
              @for (p of t.proximos; track p.mes) {
                <li><span>{{ mesCorto(p.mes) }}</span><span class="num">{{ p.monto | monto }}</span></li>
              }
            </ul>
          }
        </section>

        <form class="tarjeta formulario" (ngSubmit)="pagar(t)">
          <h2>Pagar resumen</h2>
          <p class="atenuado chico">Cargá lo que pagaste de verdad. Ese pago es el gasto del mes y baja la deuda; si pagás menos, el resto queda pendiente.</p>
          <label class="campo">De la plata del mes
            <input id="pago-mes" name="pagoMes" inputmode="decimal" class="num" placeholder="0" [(ngModel)]="pagoMes" />
          </label>
          <label class="campo">De ahorros (ahorro libre: {{ resumen()?.saldos?.ahorro_libre | monto }})
            <input id="pago-ahorros" name="pagoAhorros" inputmode="decimal" class="num" placeholder="0" [(ngModel)]="pagoAhorros" />
          </label>
          <button type="submit" class="boton boton-primario" [disabled]="guardando()">Registrar pago</button>
          @if (aviso()) { <p class="ingreso chico" role="status">{{ aviso() }}</p> }
        </form>

        <section class="seccion" aria-labelledby="compras-titulo">
          <h2 id="compras-titulo">Compras anotadas</h2>
          @if (compras().length) {
            <ul class="lista">
              @for (c of compras(); track c.id) {
                <li class="compra">
                  <span class="pila">
                    <span class="nombre">{{ c.descripcion || catalogo.nombresCategoria().get(c.categoria_id ?? '') || 'Compra' }}</span>
                    <span class="atenuado chico">
                      @if (c.cantidad_cuotas > 1) {
                        Cuota {{ cuotaActual(c, t.mes_en_curso) }} de {{ c.cantidad_cuotas }} · <span class="num">{{ c.cuotas[0].monto | monto }}</span> por mes
                      } @else { 1 pago · {{ c.comprado_en }} }
                    </span>
                  </span>
                  <span class="num">{{ c.monto_total | monto }}</span>
                  <button type="button" class="boton boton-icono" (click)="eliminarCompra(c)" [attr.aria-label]="'Eliminar compra ' + (c.descripcion || '')">✕</button>
                </li>
              }
            </ul>
          } @else {
            <p class="vacio">Todavía no anotaste compras con esta tarjeta. Cargalas desde + eligiendo la tarjeta en "Pagado con".</p>
          }
        </section>

        <button type="button" class="boton" (click)="alternarActiva(t)">{{ t.activa ? 'Desactivar tarjeta' : 'Activar tarjeta' }}</button>
      } @else if (!mostrarNueva()) {
        <p class="vacio">Agregá tu tarjeta de crédito para anotar compras en cuotas y saber cuánto debés.</p>
      }

      <a routerLink="/" class="atenuado">‹ Volver al inicio</a>
    </main>
    <bi-navegacion />
  `,
  styles: `
    .formulario { display: flex; flex-direction: column; gap: 12px; }
    .dos { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
    .pila { display: flex; flex-direction: column; gap: 4px; }
    .resumenes { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
    .bloque { background: var(--bosque-2); border-radius: 16px; padding: 12px 14px; display: flex; flex-direction: column; gap: 4px; }
    .proximos { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; font-size: 13px; }
    .proximos li { display: flex; justify-content: space-between; color: var(--sobre-bosque-suave); }
    .compra { display: flex; align-items: center; gap: 10px; padding: 10px 0; }
    .compra .pila { flex: 1; min-width: 0; }
    .nombre { font-weight: 500; }
    .chico { font-size: 13px; margin: 0; }
  `,
})
export class TarjetasPagina implements OnInit {
  private readonly api = inject(ApiServicio);
  readonly catalogo = inject(CatalogoStore);

  readonly tarjetas = signal<Tarjeta[]>([]);
  readonly elegidaId = signal<string | null>(null);
  readonly compras = signal<CompraTarjeta[]>([]);
  readonly resumen = signal<Resumen | null>(null);
  readonly mostrarNueva = signal(false);
  readonly error = signal<string | null>(null);
  readonly aviso = signal<string | null>(null);
  readonly guardando = signal(false);
  readonly cuotaActual = cuotaActual;
  readonly mesCorto = mesCorto;

  readonly elegida = computed(() => this.tarjetas().find((t) => t.id === this.elegidaId()) ?? this.tarjetas()[0]);

  nombreNueva = '';
  cierreNueva = 25;
  vencimientoNueva = 5;
  pagoMes = '';
  pagoAhorros = '';

  ngOnInit(): void {
    this.catalogo.cargar();
    this.cargar();
  }

  elegir(id: string): void {
    this.elegidaId.set(id);
    this.cargarCompras(id);
  }

  crearTarjeta(): void {
    if (!this.nombreNueva.trim()) {
      this.error.set('Ponele un nombre a la tarjeta.');
      return;
    }
    this.api
      .crearTarjeta({ nombre: this.nombreNueva.trim(), dia_cierre: +this.cierreNueva, dia_vencimiento: +this.vencimientoNueva })
      .subscribe({
        next: (tarjeta) => {
          this.mostrarNueva.set(false);
          this.nombreNueva = '';
          this.elegidaId.set(tarjeta.id);
          this.cargar();
          this.catalogo.cargar();
        },
        error: (error) => this.error.set(mensajeDeError(error)),
      });
  }

  pagar(tarjeta: Tarjeta): void {
    const deMes = this.pagoMes ? montoDesdeTexto(this.pagoMes) : null;
    const deAhorros = this.pagoAhorros ? montoDesdeTexto(this.pagoAhorros) : null;
    if ((this.pagoMes && !deMes) || (this.pagoAhorros && !deAhorros) || (!deMes && !deAhorros)) {
      this.error.set('Escribí cuánto pagaste, con hasta dos decimales.');
      return;
    }
    const origenes = [
      ...(deMes ? [{ bolsillo: 'disponible' as const, monto: deMes }] : []),
      ...(deAhorros ? [{ bolsillo: 'ahorros' as const, monto: deAhorros }] : []),
    ];
    const total = origenes.reduce((suma, o) => suma + Number(o.monto), 0).toFixed(2);
    this.guardando.set(true);
    this.error.set(null);
    this.api.pagarResumen(tarjeta.id, { monto: total, ocurrido_en: fechaParaApi(hoyLocal()), origenes }).subscribe({
      next: () => {
        this.guardando.set(false);
        this.pagoMes = '';
        this.pagoAhorros = '';
        this.aviso.set('Pago registrado. Ya cuenta como gasto del mes.');
        this.cargar();
      },
      error: (error) => {
        this.guardando.set(false);
        this.error.set(mensajeDeError(error));
      },
    });
  }

  eliminarCompra(compra: CompraTarjeta): void {
    this.api.eliminarCompraTarjeta(compra.id).subscribe({
      next: () => this.cargar(),
      error: (error) => this.error.set(mensajeDeError(error)),
    });
  }

  alternarActiva(tarjeta: Tarjeta): void {
    this.api.actualizarTarjeta(tarjeta.id, { activa: !tarjeta.activa }).subscribe({
      next: () => {
        this.cargar();
        this.catalogo.cargar();
      },
      error: (error) => this.error.set(mensajeDeError(error)),
    });
  }

  private cargar(): void {
    this.api.resumen(claveMes()).subscribe((resumen) => this.resumen.set(resumen));
    this.api.tarjetas().subscribe({
      next: (tarjetas) => {
        this.tarjetas.set(tarjetas);
        const elegida = this.elegida();
        if (elegida) this.cargarCompras(elegida.id);
      },
      error: (error) => this.error.set(mensajeDeError(error)),
    });
  }

  private cargarCompras(id: string): void {
    this.api.comprasTarjeta(id).subscribe((compras) => this.compras.set(compras));
  }
}
