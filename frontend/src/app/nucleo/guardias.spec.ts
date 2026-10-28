import { TestBed } from '@angular/core/testing';
import { ActivatedRouteSnapshot, Router, RouterStateSnapshot, UrlTree, provideRouter } from '@angular/router';

import { AutenticacionServicio } from './autenticacion.servicio';
import { requiereSesion, soloSinSesion } from './guardias';

describe('guardias de sesión', () => {
  function preparar(autenticado: boolean) {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        { provide: AutenticacionServicio, useValue: { estaAutenticado: async () => autenticado } },
      ],
    });
  }

  function ejecutar(guardia: typeof requiereSesion) {
    return TestBed.runInInjectionContext(() =>
      guardia({} as ActivatedRouteSnapshot, {} as RouterStateSnapshot),
    ) as Promise<boolean | UrlTree>;
  }

  it('sin sesión, las pantallas privadas mandan al ingreso', async () => {
    preparar(false);
    const resultado = await ejecutar(requiereSesion);
    expect(TestBed.inject(Router).serializeUrl(resultado as UrlTree)).toBe('/ingreso');
  });

  it('con sesión, las pantallas privadas dejan pasar', async () => {
    preparar(true);
    expect(await ejecutar(requiereSesion)).toBeTrue();
  });

  it('con sesión, el ingreso manda al inicio', async () => {
    preparar(true);
    const resultado = await ejecutar(soloSinSesion);
    expect(TestBed.inject(Router).serializeUrl(resultado as UrlTree)).toBe('/');
  });

  it('sin sesión, el ingreso deja pasar', async () => {
    preparar(false);
    expect(await ejecutar(soloSinSesion)).toBeTrue();
  });
});
