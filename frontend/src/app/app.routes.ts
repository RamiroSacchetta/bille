import { Routes } from '@angular/router';

import { requiereSesion, soloSinSesion } from './nucleo/guardias';

export const routes: Routes = [
  {
    path: 'ingreso',
    canActivate: [soloSinSesion],
    title: 'Bille · Iniciar sesión',
    loadComponent: () => import('./funcionalidades/autenticacion/ingreso.pagina').then((m) => m.IngresoPagina),
  },
  {
    path: '',
    canActivate: [requiereSesion],
    children: [
      {
        path: '',
        title: 'Bille',
        loadComponent: () => import('./funcionalidades/inicio/inicio.pagina').then((m) => m.InicioPagina),
      },
      {
        path: 'movimientos',
        title: 'Bille · Movimientos',
        loadComponent: () => import('./funcionalidades/movimientos/movimientos.pagina').then((m) => m.MovimientosPagina),
      },
      {
        path: 'cargar',
        title: 'Bille · Carga rápida',
        loadComponent: () => import('./funcionalidades/movimientos/carga.pagina').then((m) => m.CargaPagina),
      },
      {
        path: 'ahorros',
        title: 'Bille · Ahorros',
        loadComponent: () => import('./funcionalidades/ahorros/ahorros.pagina').then((m) => m.AhorrosPagina),
      },
      {
        path: 'ahorros/:id',
        title: 'Bille · Objetivo',
        loadComponent: () => import('./funcionalidades/ahorros/objetivo.pagina').then((m) => m.ObjetivoPagina),
      },
      {
        path: 'ajustes',
        title: 'Bille · Ajustes',
        loadComponent: () => import('./funcionalidades/ajustes/ajustes.pagina').then((m) => m.AjustesPagina),
      },
    ],
  },
  { path: '**', redirectTo: '' },
];
