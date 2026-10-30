import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { entorno } from '../../environments/entorno';
import {
  Categoria,
  CompraTarjeta,
  MetodoPago,
  Movimiento,
  NuevaCompraTarjeta,
  NuevaTransferencia,
  NuevoCambio,
  NuevoGasto,
  NuevoIngreso,
  NuevoObjetivo,
  Objetivo,
  PagoResumen,
  Perfil,
  Resumen,
  Tarjeta,
  TipoMovimiento,
} from './modelos';

/** Cliente tipado de la API de Bille. */
@Injectable({ providedIn: 'root' })
export class ApiServicio {
  private readonly http = inject(HttpClient);
  private readonly url = entorno.apiUrl;

  /** Pedido liviano para despertar la API (en la nube se duerme sin uso). */
  salud(): Observable<unknown> {
    return this.http.get(`${this.url}/salud`);
  }

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

  /** Compra o venta de dólares. */
  cambiar(datos: NuevoCambio): Observable<Movimiento> {
    return this.http.post<Movimiento>(`${this.url}/movimientos/cambios`, datos);
  }

  eliminarMovimiento(id: string): Observable<void> {
    return this.http.delete<void>(`${this.url}/movimientos/${id}`);
  }

  objetivos(): Observable<Objetivo[]> {
    return this.http.get<Objetivo[]>(`${this.url}/objetivos`);
  }

  crearObjetivo(datos: NuevoObjetivo): Observable<Objetivo> {
    return this.http.post<Objetivo>(`${this.url}/objetivos`, datos);
  }

  actualizarObjetivo(id: string, cambios: Partial<Pick<Objetivo, 'nombre' | 'monto_meta' | 'fecha_meta' | 'archivado'>>): Observable<Objetivo> {
    return this.http.patch<Objetivo>(`${this.url}/objetivos/${id}`, cambios);
  }

  /** Devuelve lo apartado a lo libre y elimina el objetivo. */
  eliminarObjetivo(id: string): Observable<void> {
    return this.http.delete<void>(`${this.url}/objetivos/${id}`);
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

  tarjetas(): Observable<Tarjeta[]> {
    return this.http.get<Tarjeta[]>(`${this.url}/tarjetas`);
  }

  crearTarjeta(datos: { nombre: string; dia_cierre: number; dia_vencimiento: number }): Observable<Tarjeta> {
    return this.http.post<Tarjeta>(`${this.url}/tarjetas`, datos);
  }

  actualizarTarjeta(id: string, cambios: Partial<Pick<Tarjeta, 'nombre' | 'dia_cierre' | 'dia_vencimiento' | 'activa'>>): Observable<Tarjeta> {
    return this.http.patch<Tarjeta>(`${this.url}/tarjetas/${id}`, cambios);
  }

  comprasTarjeta(id: string): Observable<CompraTarjeta[]> {
    return this.http.get<CompraTarjeta[]>(`${this.url}/tarjetas/${id}/compras`);
  }

  registrarCompraTarjeta(id: string, datos: NuevaCompraTarjeta): Observable<CompraTarjeta> {
    return this.http.post<CompraTarjeta>(`${this.url}/tarjetas/${id}/compras`, datos);
  }

  eliminarCompraTarjeta(compraId: string): Observable<void> {
    return this.http.delete<void>(`${this.url}/tarjetas/compras/${compraId}`);
  }

  pagarResumen(id: string, datos: PagoResumen): Observable<Movimiento> {
    return this.http.post<Movimiento>(`${this.url}/tarjetas/${id}/pagos`, datos);
  }

  /** CSV de los movimientos del mes (o de todos si no se indica mes). */
  exportarMovimientos(mes?: string): Observable<Blob> {
    const params = mes ? new HttpParams().set('mes', mes) : undefined;
    return this.http.get(`${this.url}/exportar/movimientos`, { params, responseType: 'blob' });
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
