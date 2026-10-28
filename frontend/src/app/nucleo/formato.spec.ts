import { claveMes, formatearConSigno, formatearMonto, montoDesdeTexto, moverMes, nombreDia } from './formato';

describe('formato', () => {
  it('formatea montos en es-AR', () => {
    expect(formatearMonto('1250000')).toBe('$ 1.250.000');
    expect(formatearMonto('482350.5', true)).toBe('$ 482.350,50');
  });

  it('agrega el signo tipográfico', () => {
    expect(formatearConSigno('-38420')).toBe('−$ 38.420');
    expect(formatearConSigno('1000')).toBe('+$ 1.000');
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
});
