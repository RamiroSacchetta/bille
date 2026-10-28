// Configuración para desarrollo local (valores por defecto de `supabase start`).
// La clave anónima es pública por diseño: la seguridad la dan RLS y el backend.
export const entorno = {
  apiUrl: 'http://localhost:8000/api',
  supabaseUrl: 'http://127.0.0.1:54321',
  supabaseClaveAnonima:
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0',
};
