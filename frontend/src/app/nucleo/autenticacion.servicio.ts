import { Injectable, computed, signal } from '@angular/core';
import { Session, SupabaseClient, createClient } from '@supabase/supabase-js';

import { entorno } from '../../environments/entorno';

/** Sesión del usuario con Supabase Auth. El resto de la app solo usa el token. */
@Injectable({ providedIn: 'root' })
export class AutenticacionServicio {
  private readonly cliente: SupabaseClient = createClient(entorno.supabaseUrl, entorno.supabaseClaveAnonima);
  private readonly sesion = signal<Session | null>(null);
  private readonly lista: Promise<void>;

  readonly autenticado = computed(() => this.sesion() !== null);
  readonly usuarioId = computed(() => this.sesion()?.user.id ?? null);

  constructor() {
    this.lista = this.cliente.auth.getSession().then(({ data }) => this.sesion.set(data.session));
    this.cliente.auth.onAuthStateChange((_evento, sesion) => this.sesion.set(sesion));
  }

  /** Espera a que se restaure la sesión guardada antes de decidir si hay usuario. */
  async estaAutenticado(): Promise<boolean> {
    await this.lista;
    return this.autenticado();
  }

  async token(): Promise<string | null> {
    await this.lista;
    const { data } = await this.cliente.auth.getSession();
    return data.session?.access_token ?? null;
  }

  async iniciarSesion(email: string, contrasena: string): Promise<string | null> {
    const { error } = await this.cliente.auth.signInWithPassword({ email, password: contrasena });
    return error ? traducirError(error.message) : null;
  }

  async registrarse(nombre: string, email: string, contrasena: string): Promise<string | null> {
    const { data, error } = await this.cliente.auth.signUp({
      email,
      password: contrasena,
      options: { data: { nombre } },
    });
    if (error) return traducirError(error.message);
    return data.session ? null : 'Revisá tu email para confirmar la cuenta y después iniciá sesión.';
  }

  async cerrarSesion(): Promise<void> {
    await this.cliente.auth.signOut();
  }
}

function traducirError(mensaje: string): string {
  if (/invalid login credentials/i.test(mensaje)) return 'El email o la contraseña no son correctos.';
  if (/already registered/i.test(mensaje)) return 'Ya existe una cuenta con ese email.';
  if (/password should be at least/i.test(mensaje)) return 'La contraseña tiene que tener al menos 6 caracteres.';
  if (/valid email/i.test(mensaje)) return 'Escribí un email válido.';
  return 'No pudimos conectarnos. Probá de nuevo en un momento.';
}
