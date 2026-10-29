import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { ApiServicio } from './nucleo/api.servicio';
import { ColaOfflineServicio } from './nucleo/cola-offline';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet],
  template: '<router-outlet />',
})
export class AppComponent {
  constructor() {
    // En la nube la API se duerme sin uso: el primer pedido la despierta mientras se abre la app
    inject(ApiServicio).salud().subscribe({ error: () => {} });
    // Arranca la cola, que envía lo que quedó guardado en cuanto hay sesión
    inject(ColaOfflineServicio);
  }
}
