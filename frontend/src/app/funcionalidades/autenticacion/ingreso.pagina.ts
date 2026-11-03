import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import { BotonInstalarComponent } from '../../compartido/ui/boton-instalar.component';
import { AutenticacionServicio } from '../../nucleo/autenticacion.servicio';
import { LARGO_MINIMO_CONTRASENA, problemaContrasena } from './contrasena';
import { errorDeRetorno } from './retorno-google';

/** Iniciar sesión o crear una cuenta. Cada persona tiene su cuenta y sus datos separados. */
@Component({
  selector: 'bi-ingreso',
  imports: [FormsModule, BotonInstalarComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <main class="ingreso">
      <div class="marca">
        <span class="marca-logo"><span class="logo" aria-hidden="true">B</span> Bille</span>
        <h1 class="lema">Tu plata, clara y simple.</h1>
        <p>Registrá efectivo, ingresos y objetivos de ahorro en un solo lugar.</p>
        <bi-boton-instalar [sobreOscuro]="true" />
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
        @if (googleDisponible()) {
          <p class="separador" aria-hidden="true">o</p>
          <button type="button" class="boton boton-ancho boton-google" (click)="entrarConGoogle()" [disabled]="enviando()">
            Continuar con Google
          </button>
        }
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
    /* Se fija el color: la clase "ingreso" también es la utilidad global de montos que entran */
    .ingreso { min-height: 100%; display: flex; flex-direction: column; color: var(--tinta); }
    .marca { flex: 1; padding: 32px 20px 24px; display: flex; flex-direction: column; justify-content: center; gap: 14px; max-width: 560px; width: 100%; margin: 0 auto; }
    .marca-logo { display: flex; align-items: center; gap: 10px; font-size: 18px; font-weight: 700; letter-spacing: var(--tracking); }
    .logo { width: 36px; height: 36px; border-radius: var(--radio); background: var(--marino); color: var(--blanco); display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: 800; }
    /* Titular protagonista: pesado, en marino, directo sobre blanco */
    .lema { font-size: clamp(32px, 9vw, 56px); line-height: 1.08; }
    .marca p { margin: 0; font-size: 16px; line-height: 1.63; color: var(--grafito); }
    form {
      background: var(--superficie); border: 1px solid var(--linea); border-radius: var(--radio);
      box-shadow: var(--sombra); padding: 20px 16px 24px;
      display: flex; flex-direction: column; gap: 14px; width: calc(100% - 32px); max-width: 528px; margin: 0 auto 24px;
    }
    .ayuda { margin: -6px 0 0; font-size: 13px; color: var(--atenuado); }
    .separador { margin: 0; text-align: center; font-size: 13px; color: var(--atenuado); }
    .alternar { margin: 0; text-align: center; font-size: 14px; color: var(--atenuado); }
    .alternar button { min-height: 44px; border: 0; background: none; font: inherit; font-weight: 600; color: var(--acento); cursor: pointer; }
    .alternar button:hover { text-decoration: underline; }
  `,
})
export class IngresoPagina {
  private readonly autenticacion = inject(AutenticacionServicio);
  private readonly router = inject(Router);

  readonly modo = signal<'ingresar' | 'registrarse'>('ingresar');
  readonly error = signal<string | null>(null);
  readonly enviando = signal(false);
  readonly largoMinimo = LARGO_MINIMO_CONTRASENA;
  readonly googleDisponible = signal(false);

  nombre = '';
  email = '';
  contrasena = '';

  constructor() {
    this.error.set(errorDeRetorno(window.location.href));
    void this.autenticacion.googleDisponible().then((disponible) => this.googleDisponible.set(disponible));
  }

  async entrarConGoogle(): Promise<void> {
    this.enviando.set(true);
    const error = await this.autenticacion.entrarConGoogle();
    if (error) {
      this.error.set(error);
      this.enviando.set(false);
    }
  }

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
