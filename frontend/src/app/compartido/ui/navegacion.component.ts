import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';

/** Barra inferior con las secciones principales y el botón de carga rápida. */
@Component({
  selector: 'bi-navegacion',
  imports: [RouterLink, RouterLinkActive],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <nav aria-label="Principal">
      <a routerLink="/" routerLinkActive="activo" [routerLinkActiveOptions]="{ exact: true }" ariaCurrentWhenActive="page">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z" /></svg>
        Inicio
      </a>
      <a routerLink="/movimientos" routerLinkActive="activo" ariaCurrentWhenActive="page">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" /></svg>
        Movimientos
      </a>
      <a routerLink="/cargar" class="cargar" aria-label="Agregar movimiento">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14" /></svg>
      </a>
      <a routerLink="/ahorros" routerLinkActive="activo" ariaCurrentWhenActive="page">
        <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="5" /><circle cx="12" cy="12" r="1" /></svg>
        Ahorros
      </a>
      <a routerLink="/ajustes" routerLinkActive="activo" ariaCurrentWhenActive="page">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12" /><circle cx="16" cy="6" r="2" /><circle cx="10" cy="12" r="2" /><circle cx="18" cy="18" r="2" /></svg>
        Ajustes
      </a>
    </nav>
  `,
  styles: `
    nav {
      position: fixed; left: 0; right: 0; bottom: 0; z-index: 10;
      display: flex; justify-content: space-around; align-items: flex-start;
      background: var(--superficie); border-top: 1px solid var(--linea);
      padding: 10px max(8px, env(safe-area-inset-right, 0px)) calc(12px + env(safe-area-inset-bottom, 0px)) max(8px, env(safe-area-inset-left, 0px));
    }
    a {
      display: flex; flex-direction: column; align-items: center; gap: 4px;
      min-width: 56px; min-height: 44px; font-size: 11px; font-weight: 500;
      color: var(--atenuado); text-decoration: none;
    }
    a.activo { color: var(--tinta); }
    svg { width: 22px; height: 22px; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
    .cargar {
      width: 56px; height: 56px; border-radius: 28px; margin-top: -24px; justify-content: center;
      background: var(--bosque); color: var(--lima);
    }
    .cargar:hover { color: var(--lima); }
    .cargar svg { width: 26px; height: 26px; stroke-width: 2.4; }
  `,
})
export class NavegacionComponent {}
