-- Tests de borrado de cuentas: se puede borrar una cuenta con plata apartada en objetivos,
-- pero un objetivo con movimientos no se borra solo.
begin;
create extension if not exists pgtap with schema extensions;

select plan(3);

insert into auth.users (id, email, raw_user_meta_data)
values ('00000000-0000-0000-0000-0000000000a3', 'a3@ejemplo.com', '{"nombre": "Ana"}');

insert into public.objetivos (id, usuario_id, nombre, monto_meta)
values ('00000000-0000-0000-0000-0000000000f3', '00000000-0000-0000-0000-0000000000a3', 'Viaje', 1000);

-- Ingreso de 500 y 200 apartados en el objetivo
with m as (
  insert into public.movimientos (usuario_id, tipo, monto, ocurrido_en)
  values ('00000000-0000-0000-0000-0000000000a3', 'ingreso', 500, now())
  returning id, usuario_id)
insert into public.partes_movimiento (movimiento_id, usuario_id, bolsillo, monto)
select id, usuario_id, 'disponible', 500 from m;
with m as (
  insert into public.movimientos (usuario_id, tipo, monto, ocurrido_en)
  values ('00000000-0000-0000-0000-0000000000a3', 'transferencia', 200, now())
  returning id, usuario_id)
insert into public.partes_movimiento (movimiento_id, usuario_id, bolsillo, objetivo_id, monto)
select id, usuario_id, 'disponible'::public.bolsillo, null::uuid, -200 from m
union all
select id, usuario_id, 'ahorros'::public.bolsillo, '00000000-0000-0000-0000-0000000000f3', 200 from m;

set constraints all immediate;

-- 1: un objetivo con movimientos no se borra
select throws_ok(
  $$ delete from public.objetivos where id = '00000000-0000-0000-0000-0000000000f3' $$,
  '23503',
  null,
  'Un objetivo con movimientos no se puede borrar'
);

-- 2: la cuenta entera sí se borra, con sus objetivos y movimientos (las restricciones se chequean al final)
set constraints all deferred;
delete from auth.users where id = '00000000-0000-0000-0000-0000000000a3';
select lives_ok(
  $$ set constraints all immediate $$,
  'Se puede borrar una cuenta con plata apartada en objetivos'
);
select is(
  (select count(*)::int from public.movimientos where usuario_id = '00000000-0000-0000-0000-0000000000a3')
  + (select count(*)::int from public.objetivos where usuario_id = '00000000-0000-0000-0000-0000000000a3')
  + (select count(*)::int from public.partes_movimiento where usuario_id = '00000000-0000-0000-0000-0000000000a3'),
  0,
  'Al borrar la cuenta no queda nada suyo'
);

select * from finish();
rollback;
