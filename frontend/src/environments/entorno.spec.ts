import { hostServidor } from './entorno';

describe('hostServidor', () => {
  it('usa IPv4 cuando se abre desde localhost', () => {
    expect(hostServidor('localhost')).toBe('127.0.0.1');
    expect(hostServidor('')).toBe('127.0.0.1');
  });

  it('usa la IP de la PC cuando se abre desde el celular', () => {
    expect(hostServidor('192.168.0.10')).toBe('192.168.0.10');
  });
});
