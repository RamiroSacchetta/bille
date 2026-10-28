import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, from, switchMap, throwError } from 'rxjs';

import { entorno } from '../../environments/entorno';
import { AutenticacionServicio } from './autenticacion.servicio';

/** Agrega el token de la sesión a las llamadas a la API y manda al ingreso si la sesión venció. */
export const autenticacionInterceptor: HttpInterceptorFn = (pedido, siguiente) => {
  if (!pedido.url.startsWith(entorno.apiUrl)) return siguiente(pedido);

  const autenticacion = inject(AutenticacionServicio);
  const router = inject(Router);

  return from(autenticacion.token()).pipe(
    switchMap((token) =>
      siguiente(token ? pedido.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : pedido),
    ),
    catchError((error: HttpErrorResponse) => {
      if (error.status === 401) router.navigate(['/ingreso']);
      return throwError(() => error);
    }),
  );
};
