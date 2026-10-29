import { modoInstalacion } from './instalacion';

const ANDROID = 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Mobile Safari/537.36';
const IPHONE = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1';
const IPAD = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15';

describe('modoInstalacion', () => {
  it('con el pedido de instalación del navegador muestra el botón (Android, PC)', () => {
    expect(modoInstalacion({ userAgent: ANDROID, instalada: false, hayPedido: true, tactil: true })).toBe('boton');
  });

  it('en iPhone y iPad explica cómo agregarla a inicio', () => {
    expect(modoInstalacion({ userAgent: IPHONE, instalada: false, hayPedido: false, tactil: true })).toBe('ios');
    // El iPad se presenta como Mac, pero tiene pantalla táctil
    expect(modoInstalacion({ userAgent: IPAD, instalada: false, hayPedido: false, tactil: true })).toBe('ios');
  });

  it('si ya está instalada no ofrece nada', () => {
    expect(modoInstalacion({ userAgent: ANDROID, instalada: true, hayPedido: true, tactil: true })).toBe('nada');
    expect(modoInstalacion({ userAgent: IPHONE, instalada: true, hayPedido: false, tactil: true })).toBe('nada');
  });

  it('sin pedido del navegador y fuera de iOS no muestra nada', () => {
    expect(modoInstalacion({ userAgent: ANDROID, instalada: false, hayPedido: false, tactil: true })).toBe('nada');
    expect(modoInstalacion({ userAgent: IPAD, instalada: false, hayPedido: false, tactil: false })).toBe('nada');
  });
});
