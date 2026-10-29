/** Mismas reglas que Supabase Auth (`minimum_password_length` y `letters_digits` en config.toml). */
export const LARGO_MINIMO_CONTRASENA = 8;

export function problemaContrasena(contrasena: string): string | null {
  if (contrasena.length < LARGO_MINIMO_CONTRASENA) {
    return `La contraseña tiene que tener al menos ${LARGO_MINIMO_CONTRASENA} caracteres.`;
  }
  // `letters_digits` de Supabase solo cuenta letras a-z/A-Z
  if (!/[a-zA-Z]/.test(contrasena) || !/\d/.test(contrasena)) {
    return 'La contraseña tiene que tener letras y números.';
  }
  return null;
}
