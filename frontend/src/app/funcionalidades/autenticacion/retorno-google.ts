/**
 * Supabase vuelve de Google a /ingreso con el error en el hash o en la query
 * (por ejemplo, cuando el hook de invitaciones rechaza la cuenta).
 */
export function errorDeRetorno(url: string): string | null {
  const direccion = new URL(url);
  const parametros = new URLSearchParams(direccion.hash.slice(1));
  const error = parametros.get('error') ?? direccion.searchParams.get('error');
  if (!error) return null;
  const descripcion = parametros.get('error_description') ?? direccion.searchParams.get('error_description') ?? '';
  // El mensaje del hook ya está escrito para el usuario
  if (/solo por invitaci/i.test(descripcion)) return descripcion;
  return 'No pudimos entrar con Google. Probá de nuevo en un momento.';
}
