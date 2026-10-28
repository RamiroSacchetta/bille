import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { entorno } from '../../environments/entorno';
import {
  Categoria,
  MetodoPago,
  Movimiento,
  NuevaTransferencia,
  NuevoGasto,
  NuevoIngreso,
  Objetivo,
  Perfil,
  Resumen,
  TipoMovimiento,
} from './modelos';

/** Cliente tipado de la API de Bille. */
@Injectable({ providedIn: 'root' })
export class ApiServicio {
  private readonly http = inject(HttpClient);
  private readonly url = entorno.apiUrl;

  resumen(mes: string): Observable<Resumen> {
    return this.http.get<Resumen>(`${this.url}/resumen`, { params: { mes } });
  }

  movimientos(filtro: { mes?: string; tipo?: TipoMovimiento | null } = {}): Observable<Movimiento[]> {
    let params = new HttpParams();
    if (filtro.mes) params = params.set('mes', filtro.mes);
    if (filtro.tipo) params = params.set('tipo', filtro.tipo);
    return this.http.get<Movimiento[]>(`${this.url}/movimientos`, { params });
  }

  registrarGasto(datos: NuevoGasto): Observable<Movimiento> {
    return this.http.post<Movimiento>(`${this.url}/movimientos/gastos`, datos);
  }

  registrarIngreso(datos: NuevoIngreso): Observable<Movimiento> {
    return this.http.post<Movimiento>(`${this.url}/movimientos/ingresos`, datos);
  }

  transferir(datos: NuevaTransferencia): Observable<Movimiento> {
    return this.http.post<Movimiento>(`${this.url}/movimientos/transferencias`, datos);
  }

  eliminarMovimiento(id: string): Observable<void> {
    return this.http.delete<void>(`${this.url}/movimientos/${id}`);
  }

  objetivos(): Observable<Objetivo[]> {
    return this.http.get<Objetivo[]>(`${this.url}/objetivos`);
  }

  crearObjetivo(datos: { nombre: string; monto_meta: string; fecha_meta?: string | null }): Observable<Objetivo> {
    return this.http.post<Objetivo>(`${this.url}/objetivos`, datos);
  }

  actualizarObjetivo(id: string, cambios: Partial<Pick<Objetivo, 'nombre' | 'monto_meta' | 'fecha_meta' | 'archivado'>>): Observable<Objetivo> {
    return this.http.patch<Objetivo>(`${this.url}/objetivos/${id}`, cambios);
  }

  perfil(): Observable<Perfil> {
    return this.http.get<Perfil>(`${this.url}/perfil`);
  }

  actualizarPerfil(nombre_visible: string): Observable<Perfil> {
    return this.http.patch<Perfil>(`${this.url}/perfil`, { nombre_visible });
  }

  categorias(): Observable<Categoria[]> {
    return this.http.get<Categoria[]>(`${this.url}/categorias`);
  }

  crearCategoria(nombre: string, tipo: 'ingreso' | 'gasto'): Observable<Categoria> {
    return this.http.post<Categoria>(`${this.url}/categorias`, { nombre, tipo });
  }

  eliminarCategoria(id: string): Observable<void> {
    return this.http.delete<void>(`${this.url}/categorias/${id}`);
  }

  metodosPago(): Observable<MetodoPago[]> {
    return this.http.get<MetodoPago[]>(`${this.url}/metodos-pago`);
  }

  actualizarMetodoPago(id: string, activo: boolean): Observable<MetodoPago> {
    return this.http.patch<MetodoPago>(`${this.url}/metodos-pago/${id}`, { activo });
  }
}

/** Mensaje para mostrar al usuario a partir de un error de la API. */
export function mensajeDeError(error: unknown): string {
  if (error instanceof HttpErrorResponse) {
    if (error.status === 0) return 'No pudimos conectarnos con Bille. Revisá que el servidor esté corriendo.';
    const detalle = error.error?.detail;
    if (typeof detalle === 'string') return detalle;
  }
  return 'Algo salió mal. Probá de nuevo.';
}
