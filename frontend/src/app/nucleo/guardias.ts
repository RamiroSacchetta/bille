import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AutenticacionServicio } from './autenticacion.servicio';

// inject() solo funciona antes del primer await: por eso se resuelven las dependencias arriba.

/** Solo deja pasar con sesión iniciada. */
export const requiereSesion: CanActivateFn = async () => {
  const autenticacion = inject(AutenticacionServicio);
  const router = inject(Router);
  return (await autenticacion.estaAutenticado()) || router.parseUrl('/ingreso');
};

/** El ingreso no tiene sentido si ya hay sesión. */
export const soloSinSesion: CanActivateFn = async () => {
  const autenticacion = inject(AutenticacionServicio);
  const router = inject(Router);
  return !(await autenticacion.estaAutenticado()) || router.parseUrl('/');
};
