import { errorDeRetorno } from './retorno-google';

describe('retorno de Google', () => {
  it('muestra el motivo cuando Supabase rechaza la cuenta', () => {
    const url =
      'http://127.0.0.1:8080/ingreso#error=access_denied&error_code=signup_disabled' +
      '&error_description=Bille+es+solo+por+invitaci%C3%B3n.';
    expect(errorDeRetorno(url)).toBe('Bille es solo por invitación.');
  });

  it('también lee el error en la query', () => {
    expect(errorDeRetorno('http://127.0.0.1:8080/ingreso?error=server_error&error_description=Algo')).toBe(
      'No pudimos entrar con Google. Probá de nuevo en un momento.',
    );
  });

  it('sin error no muestra nada', () => {
    expect(errorDeRetorno('http://127.0.0.1:8080/ingreso')).toBeNull();
    expect(errorDeRetorno('http://127.0.0.1:8080/ingreso#access_token=abc')).toBeNull();
  });
});
