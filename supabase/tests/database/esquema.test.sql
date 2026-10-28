-- Tests del esquema: alta de perfil, aislamiento entre usuarios (RLS) y cuadre de partes.
begin;
create extension if not exists pgtap with schema extensions;

select plan(12);

-- Las validaciones de cuadre se disparan al final de cada sentencia
set constraints all immediate;

-- Dos usuarios: A y B
insert into auth.users (id, email, raw_user_meta_data)
values
  ('00000000-0000-0000-0000-00000000000a', 'a@ejemplo.com', '{"nombre": "Ana"}'),
  ('00000000-0000-0000-0000-00000000000b', 'b@ejemplo.com', '{}');

-- 1-2: el alta crea el perfil con categorías y métodos por defecto
select is(
  (select nombre_visible from public.perfiles where id = '00000000-0000-0000-0000-00000000000a'),
  'Ana',
  'El perfil toma el nombre de los metadatos'
);
select is(
  (select count(*)::int from public.categorias where usuario_id = '00000000-0000-0000-0000-00000000000b'),
  11,
  'Cada usuario nuevo recibe 11 categorías por defecto'
);

-- A partir de acá actuamos como el usuario A
set local role authenticated;
set local request.jwt.claims = '{"sub": "00000000-0000-0000-0000-00000000000a", "role": "authenticated"}';

-- 3: A solo ve sus categorías
select is(
  (select count(*)::int from public.categorias),
  11,
  'A solo ve sus propias categorías'
);

-- 4: A no puede crear datos a nombre de B
select throws_ok(
  $$ insert into public.objetivos (usuario_id, nombre, monto_meta)
     values ('00000000-0000-0000-0000-00000000000b', 'Ajeno', 1000) $$,
  '42501',
  null,
  'A no puede crear un objetivo a nombre de B'
);

-- Datos de A: objetivo, sueldo, mandar a ahorros y apartar para el viaje
insert into public.objetivos (id, usuario_id, nombre, monto_meta)
values ('00000000-0000-0000-0000-0000000000f1', '00000000-0000-0000-0000-00000000000a', 'Viaje a Bariloche', 800000);

-- 5: ingreso con una parte positiva
select lives_ok(
  $$ with m as (
       insert into public.movimientos (usuario_id, tipo, monto, ocurrido_en)
       values ('00000000-0000-0000-0000-00000000000a', 'ingreso', 1250000, now())
       returning id, usuario_id)
     insert into public.partes_movimiento (movimiento_id, usuario_id, bolsillo, monto)
     select id, usuario_id, 'disponible', 1250000 from m $$,
  'Un ingreso cuadrado se guarda'
);

-- 6: transferencia a ahorros y apartado para el objetivo
select lives_ok(
  $$ with m as (
       insert into public.movimientos (usuario_id, tipo, monto, ocurrido_en)
       values ('00000000-0000-0000-0000-00000000000a', 'transferencia', 300000, now())
       returning id, usuario_id)
     insert into public.partes_movimiento (movimiento_id, usuario_id, bolsillo, objetivo_id, monto)
     select m.id, m.usuario_id, v.bolsillo::public.bolsillo, v.objetivo_id, v.monto
     from m, (values
       ('disponible', null::uuid, -300000),
       ('ahorros', '00000000-0000-0000-0000-0000000000f1'::uuid, 300000)
     ) as v (bolsillo, objetivo_id, monto) $$,
  'Una transferencia que suma cero se guarda'
);

-- 7: gasto dividido entre plata del mes y el objetivo
select lives_ok(
  $$ with m as (
       insert into public.movimientos (usuario_id, tipo, monto, ocurrido_en, descripcion)
       values ('00000000-0000-0000-0000-00000000000a', 'gasto', 100000, now(), 'Arreglo del auto')
       returning id, usuario_id)
     insert into public.partes_movimiento (movimiento_id, usuario_id, bolsillo, objetivo_id, monto)
     select m.id, m.usuario_id, v.bolsillo::public.bolsillo, v.objetivo_id, v.monto
     from m, (values
       ('disponible', null::uuid, -50000),
       ('ahorros', '00000000-0000-0000-0000-0000000000f1'::uuid, -50000)
     ) as v (bolsillo, objetivo_id, monto) $$,
  'Un gasto dividido cuadrado se guarda'
);

-- 8: un gasto cuyas partes no suman el total se rechaza
select throws_ok(
  $$ with m as (
       insert into public.movimientos (usuario_id, tipo, monto, ocurrido_en)
       values ('00000000-0000-0000-0000-00000000000a', 'gasto', 100000, now())
       returning id, usuario_id)
     insert into public.partes_movimiento (movimiento_id, usuario_id, bolsillo, monto)
     select id, usuario_id, 'disponible', -60000 from m $$,
  '23514',
  null,
  'Un gasto descuadrado se rechaza'
);

-- 9: un movimiento sin partes se rechaza
select throws_ok(
  $$ insert into public.movimientos (usuario_id, tipo, monto, ocurrido_en)
     values ('00000000-0000-0000-0000-00000000000a', 'gasto', 5000, now()) $$,
  '23514',
  null,
  'Un movimiento sin partes se rechaza'
);

-- 10-11: saldos calculados desde las partes
select results_eq(
  $$ select disponible, ahorros, apartado from public.saldos_bolsillos $$,
  $$ values (900000.00::numeric(14, 2), 250000.00::numeric(14, 2), 250000.00::numeric(14, 2)) $$,
  'Saldos: disponible 900.000, ahorros 250.000, apartado 250.000'
);
select is(
  (select apartado from public.saldos_objetivos where objetivo_id = '00000000-0000-0000-0000-0000000000f1'),
  250000.00::numeric(14, 2),
  'El objetivo refleja lo apartado menos lo usado en el gasto'
);

-- 12: B no ve nada de A
set local request.jwt.claims = '{"sub": "00000000-0000-0000-0000-00000000000b", "role": "authenticated"}';
select is(
  (select count(*)::int from public.movimientos),
  0,
  'B no ve los movimientos de A'
);

select * from finish();
rollback;
