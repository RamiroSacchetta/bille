// Dónde están la API y Supabase según desde dónde se abrió la app.
// En la PC o en la red local (por ejemplo 192.168.0.10 desde el celular) se usan los servidores de esa misma
// máquina, con los valores por defecto de `supabase start`. En cualquier otro dominio (Vercel) se usa la nube.
// La clave anónima es pública por diseño: la seguridad la dan RLS y el backend.

export interface Entorno {
  apiUrl: string;
  supabaseUrl: string;
  supabaseClaveAnonima: string;
}

/**
 * Datos de la nube. Se completan al crear los proyectos (ver "Deploy en la nube" en el README):
 * la URL de Render, y la URL y la clave anónima (o publishable) de Supabase.
 */
export const NUBE: Entorno = {
  apiUrl: 'https://bille-api-uqvb.onrender.com/api',
  supabaseUrl: 'https://qzplxdazwuzcsqplzldb.supabase.co',
  supabaseClaveAnonima: 'sb_publishable_inbAthgJNZHPCfRYrvZ1nw_6mcutloF',
};

const CLAVE_ANONIMA_LOCAL =
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0';

/** Host de los servidores según desde dónde se abrió la app. `localhost` se fuerza a IPv4. */
export function hostServidor(hostname: string): string {
  return !hostname || hostname === 'localhost' ? '127.0.0.1' : hostname;
}

/** La PC (localhost) o una IP de red privada: 10.x, 172.16–31.x o 192.168.x. */
function esRedLocal(hostname: string): boolean {
  return (
    !hostname ||
    hostname === 'localhost' ||
    /^127\./.test(hostname) ||
    /^10\./.test(hostname) ||
    /^192\.168\./.test(hostname) ||
    /^172\.(1[6-9]|2\d|3[01])\./.test(hostname)
  );
}

export function entornoPara(hostname: string): Entorno {
  if (!esRedLocal(hostname)) return NUBE;
  const host = hostServidor(hostname);
  return {
    apiUrl: `http://${host}:8000/api`,
    supabaseUrl: `http://${host}:54321`,
    supabaseClaveAnonima: CLAVE_ANONIMA_LOCAL,
  };
}

export const entorno = entornoPara(typeof window === 'undefined' ? '' : window.location.hostname);
