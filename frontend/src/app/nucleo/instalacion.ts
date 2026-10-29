import { Injectable, computed, signal } from '@angular/core';

/**
 * Cómo ofrecer instalar Bille según el navegador:
 * - `boton`: el navegador avisó que se puede instalar (Android, PC) y un botón abre su ventana de instalación.
 * - `ios`: en iPhone y iPad no hay ese aviso; se explica cómo hacerlo desde Compartir.
 * - `nada`: ya está instalada o el navegador no permite instalarla.
 */
export type ModoInstalacion = 'boton' | 'ios' | 'nada';

export function modoInstalacion(e: { userAgent: string; instalada: boolean; hayPedido: boolean; tactil: boolean }): ModoInstalacion {
  if (e.instalada) return 'nada';
  if (e.hayPedido) return 'boton';
  // El iPad se presenta como Mac: se lo distingue por la pantalla táctil
  const ios = /iPhone|iPad|iPod/.test(e.userAgent) || (/Macintosh/.test(e.userAgent) && e.tactil);
  return ios ? 'ios' : 'nada';
}

/** El evento `beforeinstallprompt` de Chrome, Edge y Samsung Internet (no está en los tipos del DOM). */
interface PedidoInstalacion extends Event {
  prompt(): Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

@Injectable({ providedIn: 'root' })
export class InstalacionServicio {
  private readonly pedido = signal<PedidoInstalacion | null>(null);
  private readonly instalada = signal(this.abiertaComoApp());

  readonly modo = computed(() =>
    modoInstalacion({
      userAgent: typeof navigator === 'undefined' ? '' : navigator.userAgent,
      instalada: this.instalada(),
      hayPedido: this.pedido() !== null,
      tactil: typeof navigator !== 'undefined' && navigator.maxTouchPoints > 1,
    }),
  );

  constructor() {
    if (typeof window === 'undefined') return;
    window.addEventListener('beforeinstallprompt', (evento) => {
      // Sin esto el navegador muestra su propio aviso (a veces) y el botón ya no puede abrirlo
      evento.preventDefault();
      this.pedido.set(evento as PedidoInstalacion);
    });
    window.addEventListener('appinstalled', () => {
      this.pedido.set(null);
      this.instalada.set(true);
    });
  }

  /** Abre la ventana de instalación del navegador. El pedido sirve una sola vez. */
  async instalar(): Promise<void> {
    const pedido = this.pedido();
    if (!pedido) return;
    await pedido.prompt();
    const { outcome } = await pedido.userChoice;
    this.pedido.set(null);
    if (outcome === 'accepted') this.instalada.set(true);
  }

  private abiertaComoApp(): boolean {
    if (typeof window === 'undefined') return false;
    const safari = navigator as Navigator & { standalone?: boolean };
    return window.matchMedia?.('(display-mode: standalone)').matches || safari.standalone === true;
  }
}
