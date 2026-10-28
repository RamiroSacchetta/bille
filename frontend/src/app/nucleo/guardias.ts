import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AutenticacionServicio } from './autenticacion.servicio';

/** Solo deja pasar con sesión iniciada. */
export const requiereSesion: CanActivateFn = async () => {
  const autenticado = await inject(AutenticacionServicio).estaAutenticado();
  return autenticado || inject(Router).parseUrl('/ingreso');
};

/** El ingreso no tiene sentido si ya hay sesión. */
export const soloSinSesion: CanActivateFn = async () => {
  const autenticado = await inject(AutenticacionServicio).estaAutenticado();
  return !autenticado || inject(Router).parseUrl('/');
};
