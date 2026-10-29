import { NUBE, entornoPara, hostServidor } from './entorno';

describe('hostServidor', () => {
  it('usa IPv4 cuando se abre desde localhost', () => {
    expect(hostServidor('localhost')).toBe('127.0.0.1');
    expect(hostServidor('')).toBe('127.0.0.1');
  });

  it('usa la IP de la PC cuando se abre desde el celular', () => {
    expect(hostServidor('192.168.0.10')).toBe('192.168.0.10');
  });
});

describe('entornoPara', () => {
  it('en la PC o en la red local usa los servidores de esa misma máquina', () => {
    expect(entornoPara('localhost').apiUrl).toBe('http://127.0.0.1:8000/api');
    expect(entornoPara('192.168.0.10').supabaseUrl).toBe('http://192.168.0.10:54321');
    expect(entornoPara('10.0.0.5').apiUrl).toBe('http://10.0.0.5:8000/api');
    expect(entornoPara('172.20.1.2').apiUrl).toBe('http://172.20.1.2:8000/api');
  });

  it('en cualquier otro dominio usa la nube', () => {
    expect(entornoPara('bille.vercel.app')).toEqual(NUBE);
    expect(entornoPara('172.40.1.2')).toEqual(NUBE);
  });

  it('la nube va siempre por HTTPS', () => {
    expect(NUBE.apiUrl).toMatch(/^https:\/\//);
    expect(NUBE.supabaseUrl).toMatch(/^https:\/\//);
  });
});
