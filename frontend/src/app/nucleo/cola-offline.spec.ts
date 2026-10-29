import { HttpErrorResponse } from '@angular/common/http';
import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';

import { ApiServicio } from './api.servicio';
import { AutenticacionServicio } from './autenticacion.servicio';
import { AlmacenPendientes, CargaPendiente, ColaOfflineServicio } from './cola-offline';

class AlmacenEnMemoria extends AlmacenPendientes {
  readonly datos = new Map<string, CargaPendiente>();
  async todas() {
    return [...this.datos.values()];
  }
  async guardar(carga: CargaPendiente) {
    this.datos.set(carga.id, carga);
  }
  async borrar(id: string) {
    this.datos.delete(id);
  }
}

// El tipo de la respuesta no importa en estos tests: solo si el envío funcionó o no
const ok = () => of({} as any);
const sinRed = () => throwError(() => new HttpErrorResponse({ status: 0 }));
const sinSaldo = () =>
  throwError(() => new HttpErrorResponse({ status: 409, error: { detail: 'No te alcanza la plata del mes para este movimiento' } }));

describe('ColaOfflineServicio', () => {
  let almacen: AlmacenEnMemoria;
  let api: jasmine.SpyObj<ApiServicio>;
  const usuarioId = signal<string | null>('ana');

  beforeEach(() => {
    almacen = new AlmacenEnMemoria();
    api = jasmine.createSpyObj<ApiServicio>('ApiServicio', ['registrarGasto', 'registrarIngreso', 'registrarCompraTarjeta', 'cambiar']);
    usuarioId.set('ana');
    TestBed.configureTestingModule({
      providers: [
        { provide: AlmacenPendientes, useValue: almacen },
        { provide: ApiServicio, useValue: api },
        { provide: AutenticacionServicio, useValue: { usuarioId } },
      ],
    });
  });

  const gasto = (monto: string) => ({ tipo: 'gasto' as const, datos: { monto, ocurrido_en: '2026-10-28T12:00:00Z' } });

  it('guarda la carga en el dispositivo asociada a la cuenta', async () => {
    const cola = TestBed.inject(ColaOfflineServicio);

    await cola.agregar(gasto('100'));

    expect(cola.delUsuario().length).toBe(1);
    expect([...almacen.datos.values()][0].usuarioId).toBe('ana');
  });

  it('al volver la conexión envía las cargas en orden y las borra', async () => {
    const cola = TestBed.inject(ColaOfflineServicio);
    api.registrarGasto.and.returnValue(ok());
    api.registrarCompraTarjeta.and.returnValue(ok());
    await cola.agregar(gasto('100'));
    await cola.agregar({ tipo: 'compra_tarjeta', tarjetaId: 'visa', datos: { monto: '900', cuotas: 3, comprado_en: '2026-10-28' } });

    await cola.sincronizar();

    expect(api.registrarGasto).toHaveBeenCalledOnceWith(gasto('100').datos);
    expect(api.registrarCompraTarjeta).toHaveBeenCalledOnceWith('visa', jasmine.objectContaining({ cuotas: 3 }));
    expect(cola.delUsuario().length).toBe(0);
  });

  it('envía las compras y ventas de dólares hechas sin conexión', async () => {
    const cola = TestBed.inject(ColaOfflineServicio);
    api.cambiar.and.returnValue(ok());
    const datos = {
      operacion: 'compra' as const,
      dolares: '200',
      pesos: '240000',
      ocurrido_en: '2026-10-28T12:00:00Z',
      pesos_en: { bolsillo: 'ahorros' as const },
    };
    await cola.agregar({ tipo: 'cambio', datos });

    await cola.sincronizar();

    expect(api.cambiar).toHaveBeenCalledOnceWith(datos);
    expect(cola.delUsuario().length).toBe(0);
  });

  it('si sigue sin conexión no borra nada y deja de intentar', async () => {
    const cola = TestBed.inject(ColaOfflineServicio);
    api.registrarGasto.and.callFake(sinRed);
    await cola.agregar(gasto('100'));
    await cola.agregar(gasto('200'));

    await cola.sincronizar();

    expect(api.registrarGasto).toHaveBeenCalledTimes(1);
    expect(cola.delUsuario().length).toBe(2);
  });

  it('si el servidor la rechaza la deja con el motivo y sigue con las demás', async () => {
    const cola = TestBed.inject(ColaOfflineServicio);
    api.registrarGasto.and.returnValues(sinSaldo(), ok());
    await cola.agregar(gasto('99999999'));
    await cola.agregar(gasto('100'));

    await cola.sincronizar();

    expect(cola.delUsuario().length).toBe(1);
    expect(cola.delUsuario()[0].error).toBe('No te alcanza la plata del mes para este movimiento');
  });

  it('nunca envía las cargas de otra cuenta', async () => {
    const cola = TestBed.inject(ColaOfflineServicio);
    api.registrarGasto.and.returnValue(ok());
    await cola.agregar(gasto('100'));

    usuarioId.set('beto');
    await cola.sincronizar();

    expect(api.registrarGasto).not.toHaveBeenCalled();
    expect(almacen.datos.size).toBe(1);
  });
});
