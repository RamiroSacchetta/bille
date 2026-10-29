-- Tests de dólares: bolsillo propio, cambio entre monedas, objetivos en dólares y nada se mezcla con los pesos.
begin;
create extension if not exists pgtap with schema extensions;

select plan(11);

set constraints all immediate;

insert into auth.users (id, email, raw_user_meta_data)
values ('00000000-0000-0000-0000-0000000000a2', 'a2@ejemplo.com', '{"nombre": "Ana"}');

set local role authenticated;
set local request.jwt.claims = '{"sub": "00000000-0000-0000-0000-0000000000a2", "role": "authenticated"}';

-- Sueldo de 2.000.000 en la plata del mes
with m as (
  insert into public.movimientos (usuario_id, tipo, monto, ocurrido_en)
  values ('00000000-0000-0000-0000-0000000000a2', 'ingreso', 2000000, now())
  returning id, usuario_id)
insert into public.partes_movimiento (movimiento_id, usuario_id, bolsillo, monto)
select id, usuario_id, 'disponible'::public.bolsillo, 2000000 from m;

-- 1: comprar US$ 1.000 con $ 1.200.000 es un cambio
select lives_ok(
  $$ with m as (
       insert into public.movimientos (usuario_id, tipo, monto, moneda, ocurrido_en)
       values ('00000000-0000-0000-0000-0000000000a2', 'cambio', 1000, 'USD', now())
       returning id, usuario_id)
     insert into public.partes_movimiento (movimiento_id, usuario_id, bolsillo, monto)
     select id, usuario_id, 'disponible'::public.bolsillo, -1200000 from m
     union all
     select id, usuario_id, 'dolares'::public.bolsillo, 1000 from m $$,
  'Comprar dólares se guarda como cambio'
);

-- 2: los dólares van aparte y no suman a los pesos
select results_eq(
  $$ select disponible, ahorros, dolares from public.saldos_bolsillos $$,
  $$ values (800000.00::numeric(14, 2), 0.00::numeric(14, 2), 1000.00::numeric(14, 2)) $$,
  'Los dólares tienen su propio saldo y los pesos bajan'
);

-- 3: la parte en dólares de un cambio tiene que ser el monto del movimiento
select throws_ok(
  $$ with m as (
       insert into public.movimientos (usuario_id, tipo, monto, moneda, ocurrido_en)
       values ('00000000-0000-0000-0000-0000000000a2', 'cambio', 100, 'USD', now())
       returning id, usuario_id)
     insert into public.partes_movimiento (movimiento_id, usuario_id, bolsillo, monto)
     select id, usuario_id, 'disponible'::public.bolsillo, -120000 from m
     union all
     select id, usuario_id, 'dolares'::public.bolsillo, 90 from m $$,
  '23514',
  null,
  'Un cambio con la parte en dólares distinta del monto se rechaza'
);

-- 4: un cambio necesita una parte en pesos y otra en dólares
select throws_ok(
  $$ with m as (
       insert into public.movimientos (usuario_id, tipo, monto, moneda, ocurrido_en)
       values ('00000000-0000-0000-0000-0000000000a2', 'cambio', 100, 'USD', now())
       returning id, usuario_id)
     insert into public.partes_movimiento (movimiento_id, usuario_id, bolsillo, monto)
     select id, usuario_id, 'disponible'::public.bolsillo, -100 from m
     union all
     select id, usuario_id, 'ahorros'::public.bolsillo, 100 from m $$,
  '23514',
  null,
  'Un cambio sin parte en dólares se rechaza'
);

-- 5: una transferencia no puede mezclar monedas
select throws_ok(
  $$ with m as (
       insert into public.movimientos (usuario_id, tipo, monto, ocurrido_en)
       values ('00000000-0000-0000-0000-0000000000a2', 'transferencia', 100, now())
       returning id, usuario_id)
     insert into public.partes_movimiento (movimiento_id, usuario_id, bolsillo, monto)
     select id, usuario_id, 'disponible'::public.bolsillo, -100 from m
     union all
     select id, usuario_id, 'dolares'::public.bolsillo, 100 from m $$,
  '23514',
  null,
  'Una transferencia entre pesos y dólares se rechaza'
);

-- 6: un gasto en dólares tiene que estar marcado en dólares
select throws_ok(
  $$ with m as (
       insert into public.movimientos (usuario_id, tipo, monto, moneda, ocurrido_en)
       values ('00000000-0000-0000-0000-0000000000a2', 'gasto', 50, 'ARS', now())
       returning id, usuario_id)
     insert into public.partes_movimiento (movimiento_id, usuario_id, bolsillo, monto)
     select id, usuario_id, 'dolares'::public.bolsillo, -50 from m $$,
  '23514',
  null,
  'Un gasto que sale de dólares no puede estar en pesos'
);
select lives_ok(
  $$ with m as (
       insert into public.movimientos (usuario_id, tipo, monto, moneda, ocurrido_en)
       values ('00000000-0000-0000-0000-0000000000a2', 'gasto', 50, 'USD', now())
       returning id, usuario_id)
     insert into public.partes_movimiento (movimiento_id, usuario_id, bolsillo, monto)
     select id, usuario_id, 'dolares'::public.bolsillo, -50 from m $$,
  'Un gasto en dólares sale de los dólares'
);

-- 8: un objetivo en dólares se aparta desde los dólares
insert into public.objetivos (id, usuario_id, nombre, monto_meta, moneda)
values ('00000000-0000-0000-0000-0000000000f2', '00000000-0000-0000-0000-0000000000a2', 'Viaje', 2000, 'USD');
with m as (
  insert into public.movimientos (usuario_id, tipo, monto, moneda, ocurrido_en)
  values ('00000000-0000-0000-0000-0000000000a2', 'transferencia', 300, 'USD', now())
  returning id, usuario_id)
insert into public.partes_movimiento (movimiento_id, usuario_id, bolsillo, objetivo_id, monto)
select id, usuario_id, 'dolares'::public.bolsillo, null::uuid, -300 from m
union all
select id, usuario_id, 'dolares'::public.bolsillo, '00000000-0000-0000-0000-0000000000f2', 300 from m;
select results_eq(
  $$ select dolares, apartado_dolares, apartado from public.saldos_bolsillos $$,
  $$ values (950.00::numeric(14, 2), 300.00::numeric(14, 2), 0.00::numeric(14, 2)) $$,
  'Lo apartado en dólares se cuenta aparte de lo apartado en pesos'
);

-- 9: un objetivo en dólares no acepta pesos
select throws_ok(
  $$ with m as (
       insert into public.movimientos (usuario_id, tipo, monto, ocurrido_en)
       values ('00000000-0000-0000-0000-0000000000a2', 'transferencia', 100, now())
       returning id, usuario_id)
     insert into public.partes_movimiento (movimiento_id, usuario_id, bolsillo, objetivo_id, monto)
     select id, usuario_id, 'disponible'::public.bolsillo, null::uuid, -100 from m
     union all
     select id, usuario_id, 'ahorros'::public.bolsillo, '00000000-0000-0000-0000-0000000000f2', 100 from m $$,
  '23514',
  null,
  'Un objetivo en dólares no acepta pesos'
);

-- 10: solo pesos y dólares
select throws_ok(
  $$ insert into public.objetivos (usuario_id, nombre, monto_meta, moneda)
     values ('00000000-0000-0000-0000-0000000000a2', 'Euros', 100, 'EUR') $$,
  '23514',
  null,
  'Las monedas posibles son pesos y dólares'
);

-- 11: el pago de una tarjeta es en pesos
insert into public.tarjetas (id, usuario_id, nombre, dia_cierre, dia_vencimiento)
values ('00000000-0000-0000-0000-0000000000c2', '00000000-0000-0000-0000-0000000000a2', 'Visa', 25, 5);
select throws_ok(
  $$ with m as (
       insert into public.movimientos (usuario_id, tipo, monto, moneda, ocurrido_en, tarjeta_id)
       values ('00000000-0000-0000-0000-0000000000a2', 'gasto', 10, 'USD', now(), '00000000-0000-0000-0000-0000000000c2')
       returning id, usuario_id)
     insert into public.partes_movimiento (movimiento_id, usuario_id, bolsillo, monto)
     select id, usuario_id, 'dolares'::public.bolsillo, -10 from m $$,
  '23514',
  null,
  'El pago de una tarjeta no puede ser en dólares'
);

select * from finish();
rollback;
