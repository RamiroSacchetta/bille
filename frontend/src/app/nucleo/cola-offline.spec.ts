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

    expect(api.registrarGasto).toHaveBeenCalledOnceWith(jasmine.objectContaining(gasto('100').datos));
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

    expect(api.cambiar).toHaveBeenCalledOnceWith(jasmine.objectContaining(datos));
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

  it('cada carga lleva un id único que se manda al servidor', async () => {
    const cola = TestBed.inject(ColaOfflineServicio);
    api.registrarGasto.and.returnValue(ok());
    await cola.agregar(gasto('100'));
    await cola.agregar(gasto('100'));
    const ids = [...almacen.datos.values()].map((c) => (c.datos as { id_carga?: string }).id_carga);

    await cola.sincronizar();

    expect(ids[0]).toMatch(/^[0-9a-f-]{36}$/);
    expect(ids[1]).not.toBe(ids[0]);
    expect(api.registrarGasto.calls.allArgs().map(([datos]) => datos.id_carga)).toEqual(ids);
  });

  describe('guardar primero, enviar después', () => {
    it('guarda la carga antes de enviarla y la borra cuando el servidor confirma', async () => {
      const cola = TestBed.inject(ColaOfflineServicio);
      let guardadaAntesDeEnviar = false;
      api.registrarGasto.and.callFake(() => {
        guardadaAntesDeEnviar = almacen.datos.size === 1;
        return ok();
      });

      const resultado = await cola.guardarYEnviar(gasto('100'));

      expect(guardadaAntesDeEnviar).toBeTrue();
      expect(resultado).toEqual({ estado: 'enviada' });
      expect(almacen.datos.size).toBe(0);
    });

    it('sin respuesta del servidor la deja guardada para enviarla después', async () => {
      const cola = TestBed.inject(ColaOfflineServicio);
      api.registrarGasto.and.callFake(sinRed);

      const resultado = await cola.guardarYEnviar(gasto('100'));

      expect(resultado).toEqual({ estado: 'pendiente' });
      expect(cola.delUsuario().length).toBe(1);
    });

    it('si el servidor la rechaza la saca de la cola y devuelve el motivo', async () => {
      const cola = TestBed.inject(ColaOfflineServicio);
      api.registrarGasto.and.callFake(sinSaldo);

      const resultado = await cola.guardarYEnviar(gasto('99999999'));

      expect(resultado).toEqual({ estado: 'rechazada', error: 'No te alcanza la plata del mes para este movimiento' });
      expect(almacen.datos.size).toBe(0);
    });

    it('al abrir la app con sesión envía lo que quedó guardado', async () => {
      almacen.datos.set('000-1', {
        id: '000-1',
        usuarioId: 'ana',
        creadaEn: '2026-10-28T12:00:00Z',
        ...gasto('100'),
      });
      api.registrarGasto.and.returnValue(ok());

      const cola = TestBed.inject(ColaOfflineServicio);
      TestBed.flushEffects();
      await cola.sincronizando;

      expect(api.registrarGasto).toHaveBeenCalledTimes(1);
      expect(almacen.datos.size).toBe(0);
    });
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
