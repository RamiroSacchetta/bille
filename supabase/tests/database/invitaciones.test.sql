-- Tests del registro por invitación: solo se crean cuentas para emails de la lista.
begin;
create extension if not exists pgtap with schema extensions;

select plan(5);

insert into public.invitaciones (email) values ('Ana@Ejemplo.com');

-- 1: un email invitado puede registrarse (sin importar mayúsculas)
select is(
  public.hook_antes_de_crear_usuario('{"user": {"email": "ana@ejemplo.com"}}'::jsonb),
  '{}'::jsonb,
  'Un email invitado puede crear su cuenta'
);

-- 2: un email no invitado se rechaza con 403
select is(
  public.hook_antes_de_crear_usuario('{"user": {"email": "intruso@ejemplo.com"}}'::jsonb) -> 'error' ->> 'http_code',
  '403',
  'Un email no invitado no puede crear su cuenta'
);

-- 3: sin email (por ejemplo, otro proveedor) también se rechaza
select ok(
  public.hook_antes_de_crear_usuario('{"user": {}}'::jsonb) ? 'error',
  'Sin email no se crea la cuenta'
);

-- 4: los usuarios de la app no pueden ver la lista
set local role authenticated;
select throws_ok(
  'select * from public.invitaciones',
  '42501',
  null,
  'Los usuarios no pueden leer las invitaciones'
);

-- 5: ni llamar al hook
select throws_ok(
  $$select public.hook_antes_de_crear_usuario('{}'::jsonb)$$,
  '42501',
  null,
  'Los usuarios no pueden ejecutar el hook'
);

select * from finish();
rollback;
