import { ChangeDetectionStrategy, Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { NavegacionComponent } from '../../compartido/ui/navegacion.component';
import { ApiServicio, mensajeDeError } from '../../nucleo/api.servicio';
import { AutenticacionServicio } from '../../nucleo/autenticacion.servicio';
import { CatalogoStore } from '../../nucleo/catalogo.store';
import { Categoria, MetodoPago } from '../../nucleo/modelos';

const TIPOS_METODO: Record<string, string> = {
  efectivo: 'Efectivo',
  debito: 'Tarjeta de débito',
  credito: 'Crédito',
  billetera: 'Billetera virtual',
  banco: 'Banco',
};

/** Ajustes: nombre, categorías, métodos de pago y cerrar sesión. */
@Component({
  selector: 'bi-ajustes',
  imports: [FormsModule, RouterLink, NavegacionComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <main class="pantalla">
      <h1>Ajustes</h1>

      <form class="tarjeta perfil" (ngSubmit)="guardarNombre()">
        <span class="avatar" aria-hidden="true">{{ nombre().charAt(0).toUpperCase() }}</span>
        <label class="campo nombre">Tu nombre
          <input id="ajustes-nombre" name="nombre" maxlength="80" [ngModel]="nombre()" (ngModelChange)="nombre.set($event)" />
        </label>
        <button type="submit" class="boton">Guardar</button>
      </form>

      <section class="seccion" aria-labelledby="categorias-titulo">
        <h2 id="categorias-titulo">Categorías</h2>
        <div class="chips">
          @for (categoria of catalogo.categorias(); track categoria.id) {
            <span class="categoria" [class]="categoria.tipo">
              {{ categoria.nombre }}
              <button type="button" (click)="eliminarCategoria(categoria)" [attr.aria-label]="'Eliminar categoría ' + categoria.nombre">✕</button>
            </span>
          }
        </div>
        <form class="nueva-categoria" (ngSubmit)="crearCategoria()">
          <label class="campo">Nueva categoría
            <input id="categoria-nombre" name="categoria" maxlength="60" placeholder="Ej: Mascotas" [(ngModel)]="nuevaCategoria" />
          </label>
          <div class="segmentado" role="group" aria-label="Tipo de categoría">
            <button type="button" [attr.aria-pressed]="tipoCategoria() === 'gasto'" (click)="tipoCategoria.set('gasto')">Gasto</button>
            <button type="button" [attr.aria-pressed]="tipoCategoria() === 'ingreso'" (click)="tipoCategoria.set('ingreso')">Ingreso</button>
          </div>
          <button type="submit" class="boton">Agregar</button>
        </form>
      </section>

      <section class="seccion" aria-labelledby="metodos-titulo">
        <h2 id="metodos-titulo">Métodos de pago</h2>
        <ul class="lista">
          @for (metodo of catalogo.metodos(); track metodo.id) {
            <li>
              <label class="metodo" [for]="'metodo-' + metodo.id">
                <span class="pila"><span>{{ metodo.nombre }}</span><span class="atenuado chico">{{ tipos[metodo.tipo] }}</span></span>
                <input type="checkbox" [id]="'metodo-' + metodo.id" [checked]="metodo.activo" (change)="alternarMetodo(metodo)" />
              </label>
            </li>
          }
        </ul>
      </section>

      <a routerLink="/tarjetas" class="tarjeta enlace">Tarjetas de crédito <span aria-hidden="true">›</span></a>

      @if (error()) { <p class="error" role="alert">{{ error() }}</p> }
      @if (aviso()) { <p class="atenuado" role="status">{{ aviso() }}</p> }

      <button type="button" class="boton boton-peligro" (click)="cerrarSesion()">Cerrar sesión</button>
    </main>
    <bi-navegacion />
  `,
  styles: `
    .perfil { display: flex; align-items: flex-end; gap: 12px; flex-wrap: wrap; }
    .avatar { width: 52px; height: 52px; border-radius: 26px; background: var(--lima); color: var(--bosque); display: flex; align-items: center; justify-content: center; font-size: 20px; font-weight: 700; }
    .nombre { flex: 1; min-width: 160px; }
    .categoria { min-height: 40px; padding: 0 4px 0 12px; border-radius: 20px; display: inline-flex; align-items: center; gap: 2px; font-size: 14px; font-weight: 500; }
    .categoria.gasto { background: var(--gasto-fondo); color: #8a3409; }
    .categoria.ingreso { background: var(--ingreso-fondo); color: #084c80; }
    .categoria button { width: 36px; height: 36px; border: 0; background: none; color: inherit; cursor: pointer; border-radius: 18px; }
    .nueva-categoria { display: flex; flex-direction: column; gap: 10px; }
    .metodo { display: flex; justify-content: space-between; align-items: center; min-height: 52px; gap: 12px; }
    .metodo input { width: 22px; height: 22px; accent-color: var(--bosque); }
    .pila { display: flex; flex-direction: column; gap: 2px; }
    .chico { font-size: 12px; }
    .enlace { display: flex; justify-content: space-between; align-items: center; min-height: 44px; text-decoration: none; color: var(--tinta); font-weight: 500; }
  `,
})
export class AjustesPagina implements OnInit {
  private readonly api = inject(ApiServicio);
  private readonly autenticacion = inject(AutenticacionServicio);
  private readonly router = inject(Router);
  readonly catalogo = inject(CatalogoStore);

  readonly tipos = TIPOS_METODO;
  readonly nombre = signal('');
  readonly tipoCategoria = signal<'gasto' | 'ingreso'>('gasto');
  readonly error = signal<string | null>(null);
  readonly aviso = signal<string | null>(null);
  readonly hayCategorias = computed(() => this.catalogo.categorias().length > 0);
  nuevaCategoria = '';

  ngOnInit(): void {
    this.catalogo.cargar();
    this.api.perfil().subscribe((perfil) => this.nombre.set(perfil.nombre_visible));
  }

  guardarNombre(): void {
    this.api.actualizarPerfil(this.nombre()).subscribe({
      next: () => this.mostrarAviso('Nombre guardado.'),
      error: (error) => this.error.set(mensajeDeError(error)),
    });
  }

  crearCategoria(): void {
    if (!this.nuevaCategoria.trim()) return;
    this.api.crearCategoria(this.nuevaCategoria.trim(), this.tipoCategoria()).subscribe({
      next: () => {
        this.nuevaCategoria = '';
        this.catalogo.cargar();
        this.mostrarAviso('Categoría agregada.');
      },
      error: (error) => this.error.set(mensajeDeError(error)),
    });
  }

  eliminarCategoria(categoria: Categoria): void {
    this.api.eliminarCategoria(categoria.id).subscribe({
      next: () => {
        this.catalogo.cargar();
        this.mostrarAviso(`Categoría "${categoria.nombre}" eliminada. Sus movimientos quedan sin categoría.`);
      },
      error: (error) => this.error.set(mensajeDeError(error)),
    });
  }

  alternarMetodo(metodo: MetodoPago): void {
    this.api.actualizarMetodoPago(metodo.id, !metodo.activo).subscribe({
      next: () => this.catalogo.cargar(),
      error: (error) => this.error.set(mensajeDeError(error)),
    });
  }

  async cerrarSesion(): Promise<void> {
    await this.autenticacion.cerrarSesion();
    await this.router.navigateByUrl('/ingreso');
  }

  private mostrarAviso(texto: string): void {
    this.error.set(null);
    this.aviso.set(texto);
  }
}
