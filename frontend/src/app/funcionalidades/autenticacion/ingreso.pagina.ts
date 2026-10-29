import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import { AutenticacionServicio } from '../../nucleo/autenticacion.servicio';
import { LARGO_MINIMO_CONTRASENA, problemaContrasena } from './contrasena';

/** Iniciar sesión o crear una cuenta. Cada persona tiene su cuenta y sus datos separados. */
@Component({
  selector: 'bi-ingreso',
  imports: [FormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <main class="ingreso">
      <div class="marca">
        <span class="logo" aria-hidden="true">B</span>
        <h1>Tu plata,<br />clara y simple.</h1>
        <p>Registrá efectivo, ingresos y objetivos de ahorro en un solo lugar.</p>
      </div>
      <form (ngSubmit)="enviar()">
        <h2>{{ modo() === 'ingresar' ? 'Iniciar sesión' : 'Crear cuenta' }}</h2>
        @if (modo() === 'registrarse') {
          <label class="campo">Tu nombre
            <input id="ingreso-nombre" name="nombre" [(ngModel)]="nombre" autocomplete="given-name" required />
          </label>
        }
        <label class="campo">Correo electrónico
          <input id="ingreso-email" name="email" type="email" [(ngModel)]="email" autocomplete="email" required />
        </label>
        <label class="campo">Contraseña
          <input id="ingreso-contrasena" name="contrasena" type="password" [(ngModel)]="contrasena"
            [attr.minlength]="modo() === 'registrarse' ? largoMinimo : null"
            [autocomplete]="modo() === 'ingresar' ? 'current-password' : 'new-password'" required />
        </label>
        @if (modo() === 'registrarse') {
          <p class="ayuda">Al menos {{ largoMinimo }} caracteres, con letras y números.</p>
        }
        @if (error()) { <p class="error" role="alert">{{ error() }}</p> }
        <button type="submit" class="boton boton-primario boton-ancho" [disabled]="enviando()">
          {{ modo() === 'ingresar' ? 'Ingresar' : 'Crear cuenta' }}
        </button>
        <p class="alternar">
          @if (modo() === 'ingresar') {
            ¿No tenés cuenta? <button type="button" (click)="cambiarModo()">Creá una</button>
          } @else {
            ¿Ya tenés cuenta? <button type="button" (click)="cambiarModo()">Iniciá sesión</button>
          }
        </p>
      </form>
    </main>
  `,
  styles: `
    .ingreso { min-height: 100%; display: flex; flex-direction: column; background: var(--bosque); color: var(--sobre-bosque); }
    .marca { flex: 1; padding: 64px 28px 32px; display: flex; flex-direction: column; gap: 18px; max-width: 560px; width: 100%; margin: 0 auto; }
    .logo { width: 56px; height: 56px; border-radius: 18px; background: var(--lima); color: var(--bosque); display: flex; align-items: center; justify-content: center; font-size: 28px; font-weight: 700; }
    h1 { font-size: 40px; letter-spacing: -0.02em; line-height: 1.05; }
    .marca p { margin: 0; font-size: 16px; color: var(--sobre-bosque-suave); line-height: 1.5; }
    form { background: var(--fondo); color: var(--tinta); border-radius: 28px 28px 0 0; padding: 28px 24px 36px; display: flex; flex-direction: column; gap: 14px; width: 100%; max-width: 560px; margin: 0 auto; }
    .ayuda { margin: -6px 0 0; font-size: 13px; color: var(--atenuado); }
    .alternar { margin: 0; text-align: center; font-size: 14px; color: var(--atenuado); }
    .alternar button { min-height: 44px; border: 0; background: none; font: inherit; font-weight: 600; color: var(--tinta); text-decoration: underline; cursor: pointer; }
  `,
})
export class IngresoPagina {
  private readonly autenticacion = inject(AutenticacionServicio);
  private readonly router = inject(Router);

  readonly modo = signal<'ingresar' | 'registrarse'>('ingresar');
  readonly error = signal<string | null>(null);
  readonly enviando = signal(false);
  readonly largoMinimo = LARGO_MINIMO_CONTRASENA;

  nombre = '';
  email = '';
  contrasena = '';

  cambiarModo(): void {
    this.modo.update((m) => (m === 'ingresar' ? 'registrarse' : 'ingresar'));
    this.error.set(null);
  }

  async enviar(): Promise<void> {
    if (!this.email || !this.contrasena || (this.modo() === 'registrarse' && !this.nombre.trim())) {
      this.error.set('Completá todos los campos.');
      return;
    }
    // Las cuentas viejas pueden tener contraseñas de 6: las reglas nuevas solo valen al crear la cuenta
    const problema = this.modo() === 'registrarse' ? problemaContrasena(this.contrasena) : null;
    if (problema) {
      this.error.set(problema);
      return;
    }
    this.enviando.set(true);
    const error =
      this.modo() === 'ingresar'
        ? await this.autenticacion.iniciarSesion(this.email, this.contrasena)
        : await this.autenticacion.registrarse(this.nombre.trim(), this.email, this.contrasena);
    this.enviando.set(false);
    if (error) {
      this.error.set(error);
      return;
    }
    await this.router.navigateByUrl('/');
  }
}
