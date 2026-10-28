// Configuración para correr en la red local (valores por defecto de `supabase start`).
// La API y Supabase se buscan en la misma máquina desde la que se abrió la app, así funciona
// tanto en la PC (localhost) como desde el celular (por ejemplo 192.168.0.10).
// La clave anónima es pública por diseño: la seguridad la dan RLS y el backend.

/** Host de los servidores según desde dónde se abrió la app. `localhost` se fuerza a IPv4. */
export function hostServidor(hostname: string): string {
  return !hostname || hostname === 'localhost' ? '127.0.0.1' : hostname;
}

const host = hostServidor(typeof window === 'undefined' ? '' : window.location.hostname);

export const entorno = {
  apiUrl: `http://${host}:8000/api`,
  supabaseUrl: `http://${host}:54321`,
  supabaseClaveAnonima:
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0',
};
