-- Tests del id de carga: el mismo id no se puede guardar dos veces para el mismo usuario.
begin;
create extension if not exists pgtap with schema extensions;

select plan(4);

insert into auth.users (id, email, raw_user_meta_data)
values
  ('00000000-0000-0000-0000-0000000000a4', 'a4@ejemplo.com', '{"nombre": "Ana"}'),
  ('00000000-0000-0000-0000-0000000000b4', 'b4@ejemplo.com', '{"nombre": "Beto"}');

insert into public.movimientos (usuario_id, tipo, monto, ocurrido_en, id_carga)
values ('00000000-0000-0000-0000-0000000000a4', 'ingreso', 100, now(), '00000000-0000-0000-0000-00000000c4a1');

-- 1: el mismo id de carga no entra dos veces
select throws_ok(
  $$ insert into public.movimientos (usuario_id, tipo, monto, ocurrido_en, id_carga)
     values ('00000000-0000-0000-0000-0000000000a4', 'ingreso', 100, now(), '00000000-0000-0000-0000-00000000c4a1') $$,
  '23505',
  null,
  'Un movimiento con el mismo id de carga se rechaza'
);

-- 2: otro usuario puede tener el mismo id (lo genera cada dispositivo)
select lives_ok(
  $$ insert into public.movimientos (usuario_id, tipo, monto, ocurrido_en, id_carga)
     values ('00000000-0000-0000-0000-0000000000b4', 'ingreso', 100, now(), '00000000-0000-0000-0000-00000000c4a1') $$,
  'El id de carga es único por usuario'
);

-- 3: sin id de carga se puede repetir, como siempre
select lives_ok(
  $$ insert into public.movimientos (usuario_id, tipo, monto, ocurrido_en)
     values ('00000000-0000-0000-0000-0000000000a4', 'ingreso', 100, now()),
            ('00000000-0000-0000-0000-0000000000a4', 'ingreso', 100, now()) $$,
  'Los movimientos sin id de carga no se limitan'
);

-- 4: lo mismo para las compras con tarjeta
insert into public.tarjetas (id, usuario_id, nombre, dia_cierre, dia_vencimiento)
values ('00000000-0000-0000-0000-0000000000c4', '00000000-0000-0000-0000-0000000000a4', 'Visa', 25, 5);
insert into public.compras_tarjeta (usuario_id, tarjeta_id, monto_total, cantidad_cuotas, comprado_en, id_carga)
values ('00000000-0000-0000-0000-0000000000a4', '00000000-0000-0000-0000-0000000000c4', 100, 1, '2026-10-10',
        '00000000-0000-0000-0000-00000000c4a2');
select throws_ok(
  $$ insert into public.compras_tarjeta (usuario_id, tarjeta_id, monto_total, cantidad_cuotas, comprado_en, id_carga)
     values ('00000000-0000-0000-0000-0000000000a4', '00000000-0000-0000-0000-0000000000c4', 100, 1, '2026-10-10',
             '00000000-0000-0000-0000-00000000c4a2') $$,
  '23505',
  null,
  'Una compra con el mismo id de carga se rechaza'
);

select * from finish();
rollback;
