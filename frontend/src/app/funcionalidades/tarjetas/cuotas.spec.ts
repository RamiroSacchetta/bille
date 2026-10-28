import { CompraTarjeta } from '../../nucleo/modelos';
import { cuotaActual, mesCorto, textoCuotas } from './cuotas';

describe('cuotas', () => {
  it('muestra la vista previa de las cuotas', () => {
    expect(textoCuotas(900000, 3)).toBe('3 cuotas de $ 300.000');
    expect(textoCuotas(50000, 1)).toBe('1 pago de $ 50.000');
    expect(textoCuotas(0, 3)).toBe('');
  });

  it('calcula la cuota que toca en el resumen en curso', () => {
    const compra: CompraTarjeta = {
      id: 'c1',
      tarjeta_id: 't1',
      descripcion: 'Heladera',
      categoria_id: null,
      monto_total: '900000.00',
      cantidad_cuotas: 3,
      comprado_en: '2026-10-10',
      cuotas: [
        { numero: 1, monto: '300000.00', mes_resumen: '2026-10-01' },
        { numero: 2, monto: '300000.00', mes_resumen: '2026-11-01' },
        { numero: 3, monto: '300000.00', mes_resumen: '2026-12-01' },
      ],
    };
    expect(cuotaActual(compra, '2026-09-01')).toBe(1);
    expect(cuotaActual(compra, '2026-11-01')).toBe(2);
    expect(cuotaActual(compra, '2027-03-01')).toBe(3);
  });

  it('nombra el mes del resumen', () => {
    expect(mesCorto('2026-11-01')).toBe('nov 2026');
  });
});
