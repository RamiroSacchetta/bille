-- Tests del perfil inicial según cómo se creó la cuenta.
begin;
create extension if not exists pgtap with schema extensions;

select plan(3);

insert into auth.users (id, email, raw_user_meta_data)
values
  ('00000000-0000-0000-0000-0000000000e1', 'lucia@ejemplo.com', '{"full_name": "Lucía Pérez", "name": "Lucía Pérez"}'),
  ('00000000-0000-0000-0000-0000000000e2', 'pablo@ejemplo.com', '{"nombre": "Pablo"}'),
  ('00000000-0000-0000-0000-0000000000e3', 'sin.nombre@ejemplo.com', '{}');

-- 1: con Google se usa el nombre de pila
select is(
  (select nombre_visible from public.perfiles where id = '00000000-0000-0000-0000-0000000000e1'),
  'Lucía',
  'Con Google el perfil usa el nombre de pila'
);

-- 2: con email y contraseña se usa el nombre escrito al registrarse
select is(
  (select nombre_visible from public.perfiles where id = '00000000-0000-0000-0000-0000000000e2'),
  'Pablo',
  'Con email se usa el nombre del registro'
);

-- 3: sin nombre se usa el inicio del email
select is(
  (select nombre_visible from public.perfiles where id = '00000000-0000-0000-0000-0000000000e3'),
  'sin.nombre',
  'Sin nombre se usa el inicio del email'
);

select * from finish();
rollback;
