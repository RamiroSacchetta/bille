import {
  claveMes,
  codigoMoneda,
  fijarMonedaPrincipal,
  formatearConSigno,
  formatearMonto,
  montoDesdeTexto,
  moverMes,
  nombreDia,
  nombreMoneda,
  precioPorDolar,
  textosCambio,
} from './formato';
import { Movimiento } from './modelos';

describe('formato', () => {
  afterEach(() => fijarMonedaPrincipal('ARS'));

  it('muestra la moneda principal elegida en lugar de los pesos', () => {
    fijarMonedaPrincipal('BRL');
    expect(formatearMonto('1250000')).toBe('R$ 1.250.000');
    expect(formatearConSigno('-50,5'.replace(',', '.'), 'ARS')).toBe('−R$ 50,5');
    expect(codigoMoneda('ARS')).toBe('BRL');
    expect(nombreMoneda('ARS')).toBe('reales');

    fijarMonedaPrincipal('EUR');
    expect(formatearMonto('20.5', 'ARS', true)).toBe('€ 20,50');
    expect(nombreMoneda('ARS')).toBe('euros');
  });

  it('muestra los yenes sin decimales', () => {
    fijarMonedaPrincipal('JPY');
    expect(formatearMonto('1500.75')).toBe('¥ 1.501');
    expect(formatearMonto('1500', 'ARS', true)).toBe('¥ 1.500');
    expect(nombreMoneda('ARS')).toBe('yenes');
  });

  it('los dólares no cambian con la moneda principal', () => {
    fijarMonedaPrincipal('EUR');
    expect(formatearMonto('1500', 'USD')).toBe('US$ 1.500');
    expect(codigoMoneda('USD')).toBe('USD');
    expect(nombreMoneda('USD')).toBe('dólares');
  });

  it('formatea montos en es-AR', () => {
    expect(formatearMonto('1250000')).toBe('$ 1.250.000');
    expect(formatearMonto('482350.5', 'ARS', true)).toBe('$ 482.350,50');
  });

  it('agrega el signo tipográfico', () => {
    expect(formatearConSigno('-38420')).toBe('−$ 38.420');
    expect(formatearConSigno('1000')).toBe('+$ 1.000');
  });

  it('muestra los dólares con US$ y los pesos con $', () => {
    expect(formatearMonto('1500', 'USD')).toBe('US$ 1.500');
    expect(formatearMonto('1500', 'ARS')).toBe('$ 1.500');
    expect(formatearMonto('20.5', 'USD', true)).toBe('US$ 20,50');
    expect(formatearConSigno('-200', 'USD')).toBe('−US$ 200');
    expect(formatearConSigno('200', 'USD')).toBe('+US$ 200');
  });

  it('interpreta lo que escribe el usuario', () => {
    expect(montoDesdeTexto('1.250.000,50')).toBe('1250000.50');
    expect(montoDesdeTexto('$ 100000')).toBe('100000');
    expect(montoDesdeTexto('0')).toBeNull();
    expect(montoDesdeTexto('12,345')).toBeNull();
    expect(montoDesdeTexto('abc')).toBeNull();
  });

  it('mueve meses cruzando el año', () => {
    expect(moverMes('2026-12', 1)).toBe('2027-01');
    expect(moverMes('2026-01', -1)).toBe('2025-12');
    expect(claveMes(new Date(2026, 9, 28))).toBe('2026-10');
  });

  it('nombra los días relativos', () => {
    const hoy = new Date(2026, 9, 28, 12);
    expect(nombreDia(new Date(2026, 9, 28, 8), hoy)).toBe('Hoy');
    expect(nombreDia(new Date(2026, 9, 27, 23), hoy)).toBe('Ayer');
  });

  it('calcula a cuánto salió cada dólar', () => {
    expect(precioPorDolar(200, 240000)).toBe(1200);
    expect(precioPorDolar(3, 3700)).toBe(1233.33);
    expect(precioPorDolar(0, 1000)).toBeNull();
    expect(precioPorDolar(100, 0)).toBeNull();
  });

  describe('textos de un cambio', () => {
    const cambio = (dolares: string, pesos: string, bolsillo: 'disponible' | 'ahorros' = 'disponible') =>
      ({
        tipo: 'cambio',
        moneda: 'USD',
        monto: dolares.replace('-', ''),
        partes: [
          { bolsillo: 'dolares', monto: dolares },
          { bolsillo, monto: pesos },
        ],
      }) as unknown as Movimiento;

    it('una compra dice cuántos dólares, cuántos pesos y el precio', () => {
      expect(textosCambio(cambio('200', '-240000'))).toEqual({
        titulo: 'Compraste US$ 200',
        detalle: '$ 240.000 · $ 1.200 por dólar',
      });
    });

    it('una venta se lee al revés', () => {
      expect(textosCambio(cambio('-100', '125000', 'ahorros'))).toEqual({
        titulo: 'Vendiste US$ 100',
        detalle: '$ 125.000 · $ 1.250 por dólar',
      });
    });
  });
});
