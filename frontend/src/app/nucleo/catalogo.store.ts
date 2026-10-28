import { Injectable, computed, inject, signal } from '@angular/core';
import { forkJoin } from 'rxjs';

import { ApiServicio } from './api.servicio';
import { Categoria, MetodoPago, Objetivo } from './modelos';

/** Categorías, métodos de pago y objetivos del usuario, compartidos entre pantallas. */
@Injectable({ providedIn: 'root' })
export class CatalogoStore {
  private readonly api = inject(ApiServicio);

  readonly categorias = signal<Categoria[]>([]);
  readonly metodos = signal<MetodoPago[]>([]);
  readonly objetivos = signal<Objetivo[]>([]);

  readonly nombresCategoria = computed(() => new Map(this.categorias().map((c) => [c.id, c.nombre])));
  readonly nombresMetodo = computed(() => new Map(this.metodos().map((m) => [m.id, m.nombre])));
  readonly objetivosActivos = computed(() => this.objetivos().filter((o) => !o.archivado));

  cargar(): void {
    forkJoin({
      categorias: this.api.categorias(),
      metodos: this.api.metodosPago(),
      objetivos: this.api.objetivos(),
    }).subscribe(({ categorias, metodos, objetivos }) => {
      this.categorias.set(categorias);
      this.metodos.set(metodos);
      this.objetivos.set(objetivos);
    });
  }

  recargarObjetivos(): void {
    this.api.objetivos().subscribe((objetivos) => this.objetivos.set(objetivos));
  }
}
