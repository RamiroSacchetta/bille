import { HttpErrorResponse } from '@angular/common/http';
import { Injectable, computed, effect, inject, signal, untracked } from '@angular/core';
import { Observable, firstValueFrom } from 'rxjs';

import { ApiServicio, mensajeDeError } from './api.servicio';
import { AutenticacionServicio } from './autenticacion.servicio';
import { NuevaCompraTarjeta, NuevoCambio, NuevoGasto, NuevoIngreso } from './modelos';

/** Una carga guardada en el dispositivo hasta que el servidor la confirme. */
export type CargaPendiente = {
  id: string;
  /** Cuenta que hizo la carga: solo se envía con la sesión de esa misma cuenta. */
  usuarioId: string;
  creadaEn: string;
  error?: string | null;
} & (
  | { tipo: 'gasto'; datos: NuevoGasto }
  | { tipo: 'ingreso'; datos: NuevoIngreso }
  | { tipo: 'compra_tarjeta'; tarjetaId: string; datos: NuevaCompraTarjeta }
  | { tipo: 'cambio'; datos: NuevoCambio }
);

export type NuevaCargaPendiente =
  | { tipo: 'gasto'; datos: NuevoGasto }
  | { tipo: 'ingreso'; datos: NuevoIngreso }
  | { tipo: 'compra_tarjeta'; tarjetaId: string; datos: NuevaCompraTarjeta }
  | { tipo: 'cambio'; datos: NuevoCambio };

/** Dónde se guardan las cargas pendientes (IndexedDB en la app, memoria en los tests). */
export abstract class AlmacenPendientes {
  abstract todas(): Promise<CargaPendiente[]>;
  abstract guardar(carga: CargaPendiente): Promise<void>;
  abstract borrar(id: string): Promise<void>;
}

/** Cómo terminó el primer intento de enviar una carga recién guardada. */
export type ResultadoEnvio = { estado: 'enviada' } | { estado: 'pendiente' } | { estado: 'rechazada'; error: string };

/** Sin respuesta del servidor: la carga se puede reintentar más tarde. */
export function esErrorDeRed(error: unknown): boolean {
  return error instanceof HttpErrorResponse && error.status === 0;
}

@Injectable({ providedIn: 'root' })
export class AlmacenPendientesIndexedDb extends AlmacenPendientes {
  private base?: Promise<IDBDatabase>;

  private abrir(): Promise<IDBDatabase> {
    this.base ??= new Promise((resolver, rechazar) => {
      const pedido = indexedDB.open('bille', 1);
      pedido.onupgradeneeded = () => pedido.result.createObjectStore('pendientes', { keyPath: 'id' });
      pedido.onsuccess = () => resolver(pedido.result);
      pedido.onerror = () => rechazar(pedido.error);
    });
    return this.base;
  }

  private async operar<T>(modo: IDBTransactionMode, accion: (tabla: IDBObjectStore) => IDBRequest<T>): Promise<T> {
    const base = await this.abrir();
    return new Promise((resolver, rechazar) => {
      const pedido = accion(base.transaction('pendientes', modo).objectStore('pendientes'));
      pedido.onsuccess = () => resolver(pedido.result);
      pedido.onerror = () => rechazar(pedido.error);
    });
  }

  todas(): Promise<CargaPendiente[]> {
    return this.operar('readonly', (tabla) => tabla.getAll());
  }

  async guardar(carga: CargaPendiente): Promise<void> {
    await this.operar('readwrite', (tabla) => tabla.put(carga));
  }

  async borrar(id: string): Promise<void> {
    await this.operar('readwrite', (tabla) => tabla.delete(id));
  }
}

/**
 * Guardar primero, enviar después: toda carga se guarda en el dispositivo antes de enviarse y solo se borra
 * cuando el servidor la confirma. Lo que queda pendiente se envía al abrir la app y al volver la red.
 * Cada carga lleva un `id_carga`, así un reenvío nunca la duplica en el servidor.
 */
@Injectable({ providedIn: 'root' })
export class ColaOfflineServicio {
  private readonly almacen = inject(AlmacenPendientes);
  private readonly api = inject(ApiServicio);
  private readonly autenticacion = inject(AutenticacionServicio);
  private enviando = false;
  private secuencia = 0;
  /** La sincronización en curso (o la última), para esperarla. */
  sincronizando: Promise<void> = Promise.resolve();

  readonly pendientes = signal<CargaPendiente[]>([]);
  readonly delUsuario = computed(() =>
    this.pendientes()
      .filter((c) => c.usuarioId === this.autenticacion.usuarioId())
      // El id empieza con la hora y un contador, así el orden de envío es el de carga
      .sort((a, b) => a.id.localeCompare(b.id)),
  );

  constructor() {
    if (typeof window !== 'undefined') window.addEventListener('online', () => this.sincronizar());
    // Al abrir la app (o al iniciar sesión) se envía lo que quedó guardado
    effect(() => {
      if (this.autenticacion.usuarioId()) untracked(() => this.sincronizar());
    });
  }

  async cargar(): Promise<void> {
    this.pendientes.set(await this.almacen.todas());
  }

  async agregar(nueva: NuevaCargaPendiente): Promise<CargaPendiente> {
    const usuarioId = this.autenticacion.usuarioId();
    if (!usuarioId) throw new Error('No hay sesión para guardar la carga');
    const id = `${Date.now().toString().padStart(15, '0')}-${String(++this.secuencia).padStart(6, '0')}-${crypto.randomUUID()}`;
    const datos = { ...nueva.datos, id_carga: nueva.datos.id_carga ?? crypto.randomUUID() };
    const carga = { ...nueva, datos, id, usuarioId, creadaEn: new Date().toISOString() } as CargaPendiente;
    await this.almacen.guardar(carga);
    await this.cargar();
    return carga;
  }

  /** Guarda la carga en el dispositivo y recién después la envía. Si el servidor la rechaza, sale de la cola. */
  async guardarYEnviar(nueva: NuevaCargaPendiente): Promise<ResultadoEnvio> {
    const carga = await this.agregar(nueva);
    try {
      await firstValueFrom(this.enviar(carga));
      await this.almacen.borrar(carga.id);
      return { estado: 'enviada' };
    } catch (error) {
      if (esErrorDeRed(error)) return { estado: 'pendiente' };
      // Quien la cargó sigue en el formulario y ve el motivo: no queda pendiente
      await this.almacen.borrar(carga.id);
      return { estado: 'rechazada', error: mensajeDeError(error) };
    } finally {
      await this.cargar();
    }
  }

  async descartar(id: string): Promise<void> {
    await this.almacen.borrar(id);
    await this.cargar();
  }

  /** Envía en orden las cargas de la cuenta actual. Se detiene si sigue sin conexión. */
  sincronizar(): Promise<void> {
    if (!this.enviando) this.sincronizando = this.enviarPendientes();
    return this.sincronizando;
  }

  private async enviarPendientes(): Promise<void> {
    this.enviando = true;
    try {
      await this.cargar();
      for (const carga of this.delUsuario()) {
        try {
          await firstValueFrom(this.enviar(carga));
          await this.almacen.borrar(carga.id);
        } catch (error) {
          if (esErrorDeRed(error)) break;
          // El servidor la rechazó (por ejemplo, sin saldo): queda a la vista para que el usuario decida
          await this.almacen.guardar({ ...carga, error: mensajeDeError(error) });
        }
      }
    } finally {
      this.enviando = false;
      await this.cargar();
    }
  }

  private enviar(carga: CargaPendiente): Observable<unknown> {
    switch (carga.tipo) {
      case 'gasto':
        return this.api.registrarGasto(carga.datos);
      case 'ingreso':
        return this.api.registrarIngreso(carga.datos);
      case 'compra_tarjeta':
        return this.api.registrarCompraTarjeta(carga.tarjetaId, carga.datos);
      case 'cambio':
        return this.api.cambiar(carga.datos);
    }
  }
}
