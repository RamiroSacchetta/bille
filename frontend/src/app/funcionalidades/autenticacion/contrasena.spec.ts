import { problemaContrasena } from './contrasena';

describe('contraseña', () => {
  it('pide al menos 8 caracteres', () => {
    expect(problemaContrasena('abc1234')).toBe('La contraseña tiene que tener al menos 8 caracteres.');
  });

  it('pide letras y números', () => {
    expect(problemaContrasena('solamenteletras')).toBe('La contraseña tiene que tener letras y números.');
    expect(problemaContrasena('12345678')).toBe('La contraseña tiene que tener letras y números.');
    // Supabase solo cuenta letras sin acentos ni ñ
    expect(problemaContrasena('ñññññ123')).toBe('La contraseña tiene que tener letras y números.');
  });

  it('acepta una contraseña con 8 caracteres, letras y números', () => {
    expect(problemaContrasena('bille2026')).toBeNull();
  });
});
