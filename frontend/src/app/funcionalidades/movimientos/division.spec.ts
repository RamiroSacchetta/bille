import { Origen, estadoDivision, origenesParaApi } from './division';

describe('pago dividido', () => {
  const origenes: Origen[] = [
    { clave: 'mes', nombre: 'Plata del mes', bolsillo: 'disponible', objetivo_id: null, saldo: 482350 },
    { clave: 'libre', nombre: 'Ahorro libre', bolsillo: 'ahorros', objetivo_id: null, saldo: 475000 },
    { clave: 'viaje', nombre: 'Viaje a Bariloche', bolsillo: 'ahorros', objetivo_id: 'obj-1', saldo: 280000 },
  ];

  it('cuadra cuando las partes suman el total', () => {
    const estado = estadoDivision(100000, { mes: 50000, libre: 30000, viaje: 20000 });
    expect(estado.cuadra).toBeTrue();
    expect(estado.mensaje).toBe('Listo: las partes suman $ 100.000');
  });

  it('avisa cuánto falta o cuánto sobra', () => {
    expect(estadoDivision(100000, { mes: 50000 }).mensaje).toBe('Falta asignar $ 50.000');
    expect(estadoDivision(100000, { mes: 120000 }).mensaje).toBe('Te pasaste por $ 20.000');
  });

  it('manda solo los orígenes con monto', () => {
    expect(origenesParaApi(origenes, { mes: 50000, libre: 0, viaje: 50000 })).toEqual([
      { bolsillo: 'disponible', objetivo_id: null, monto: '50000.00' },
      { bolsillo: 'ahorros', objetivo_id: 'obj-1', monto: '50000.00' },
    ]);
  });
});
