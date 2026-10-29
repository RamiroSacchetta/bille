import { Resumen } from '../../nucleo/modelos';
import { Origen, estadoDivision, origenesDeGasto, origenesParaApi } from './division';

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

  it('habla en dólares cuando el gasto es en dólares', () => {
    expect(estadoDivision(500, { libres: 500 }, 'USD').mensaje).toBe('Listo: las partes suman US$ 500');
    expect(estadoDivision(500, { libres: 200 }, 'USD').mensaje).toBe('Falta asignar US$ 300');
    expect(estadoDivision(500, { libres: 600 }, 'USD').mensaje).toBe('Te pasaste por US$ 100');
  });

  it('manda solo los orígenes con monto', () => {
    expect(origenesParaApi(origenes, { mes: 50000, libre: 0, viaje: 50000 })).toEqual([
      { bolsillo: 'disponible', objetivo_id: null, monto: '50000.00' },
      { bolsillo: 'ahorros', objetivo_id: 'obj-1', monto: '50000.00' },
    ]);
  });

  describe('orígenes según la moneda', () => {
    const resumen = {
      saldos: { total: '1000', disponible: '600', ahorros: '400', ahorro_libre: '100', dolares: '900', dolares_libres: '700' },
      objetivos: [
        { id: 'casa', nombre: 'Casa', moneda: 'ARS', apartado: '300' },
        { id: 'viaje', nombre: 'Viaje', moneda: 'USD', apartado: '200' },
      ],
    } as unknown as Resumen;

    it('en pesos ofrece la plata del mes, el ahorro libre y solo los objetivos en pesos', () => {
      expect(origenesDeGasto(resumen, 'ARS')).toEqual([
        { clave: 'mes', nombre: 'Plata del mes', bolsillo: 'disponible', objetivo_id: null, saldo: 600 },
        { clave: 'libre', nombre: 'Ahorro libre', bolsillo: 'ahorros', objetivo_id: null, saldo: 100 },
        { clave: 'casa', nombre: 'Casa', bolsillo: 'ahorros', objetivo_id: 'casa', saldo: 300 },
      ]);
    });

    it('en dólares ofrece los dólares libres y solo los objetivos en dólares', () => {
      expect(origenesDeGasto(resumen, 'USD')).toEqual([
        { clave: 'dolares', nombre: 'Dólares libres', bolsillo: 'dolares', objetivo_id: null, saldo: 700 },
        { clave: 'viaje', nombre: 'Viaje', bolsillo: 'dolares', objetivo_id: 'viaje', saldo: 200 },
      ]);
    });

    it('sin resumen no hay orígenes', () => {
      expect(origenesDeGasto(null, 'ARS')).toEqual([]);
    });
  });
});
