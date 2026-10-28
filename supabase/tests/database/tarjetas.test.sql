-- Tests de tarjetas: la compra no mueve plata, el pago baja la deuda y cada usuario ve solo lo suyo.
begin;
create extension if not exists pgtap with schema extensions;

select plan(7);

set constraints all immediate;

insert into auth.users (id, email, raw_user_meta_data)
values
  ('00000000-0000-0000-0000-0000000000a1', 'a1@ejemplo.com', '{"nombre": "Ana"}'),
  ('00000000-0000-0000-0000-0000000000b1', 'b1@ejemplo.com', '{}');

set local role authenticated;
set local request.jwt.claims = '{"sub": "00000000-0000-0000-0000-0000000000a1", "role": "authenticated"}';

insert into public.tarjetas (id, usuario_id, nombre, dia_cierre, dia_vencimiento)
values ('00000000-0000-0000-0000-0000000000c1', '00000000-0000-0000-0000-0000000000a1', 'Visa', 25, 5);

-- Compra de 900.000 en 3 cuotas
insert into public.compras_tarjeta (id, usuario_id, tarjeta_id, descripcion, monto_total, cantidad_cuotas, comprado_en)
values ('00000000-0000-0000-0000-0000000000d1', '00000000-0000-0000-0000-0000000000a1',
        '00000000-0000-0000-0000-0000000000c1', 'Heladera', 900000, 3, '2026-10-10');
insert into public.cuotas_tarjeta (compra_id, usuario_id, tarjeta_id, numero, monto, mes_resumen)
select '00000000-0000-0000-0000-0000000000d1', '00000000-0000-0000-0000-0000000000a1',
       '00000000-0000-0000-0000-0000000000c1', n, 300000, ('2026-10-01'::date + make_interval(months => n - 1))::date
from generate_series(1, 3) as n;

-- 1: la compra no mueve plata
select is(
  (select ahorros + disponible from public.saldos_bolsillos),
  0.00::numeric(14, 2),
  'Comprar con tarjeta no cambia la plata'
);

-- 2: la deuda estimada es lo anotado
select is(
  (select deuda_estimada from public.deudas_tarjetas),
  900000.00::numeric(14, 2),
  'La deuda estimada es la suma de las cuotas'
);

-- 3: una cuota tiene que caer el día 1 del mes de resumen
select throws_ok(
  $$ insert into public.cuotas_tarjeta (compra_id, usuario_id, tarjeta_id, numero, monto, mes_resumen)
     values ('00000000-0000-0000-0000-0000000000d1', '00000000-0000-0000-0000-0000000000a1',
             '00000000-0000-0000-0000-0000000000c1', 4, 1, '2027-01-15') $$,
  '23514',
  null,
  'El mes de resumen es siempre el primer día del mes'
);

-- 4: pagar el resumen es un gasto que baja la deuda
with m as (
  insert into public.movimientos (id, usuario_id, tipo, monto, ocurrido_en)
  values ('00000000-0000-0000-0000-0000000000e0', '00000000-0000-0000-0000-0000000000a1', 'ingreso', 1000000, now())
  returning id, usuario_id)
insert into public.partes_movimiento (movimiento_id, usuario_id, bolsillo, monto)
select id, usuario_id, 'disponible', 1000000 from m;
select lives_ok(
  $$ with m as (
       insert into public.movimientos (usuario_id, tipo, monto, ocurrido_en, tarjeta_id)
       values ('00000000-0000-0000-0000-0000000000a1', 'gasto', 350000, now(), '00000000-0000-0000-0000-0000000000c1')
       returning id, usuario_id)
     insert into public.partes_movimiento (movimiento_id, usuario_id, bolsillo, monto)
     select id, usuario_id, 'disponible', -350000 from m $$,
  'El pago del resumen se guarda como gasto'
);
select is(
  (select deuda_estimada from public.deudas_tarjetas),
  550000.00::numeric(14, 2),
  'El pago baja la deuda estimada'
);

-- 6: solo un gasto puede apuntar a una tarjeta
select throws_ok(
  $$ update public.movimientos set tarjeta_id = '00000000-0000-0000-0000-0000000000c1'
     where id = '00000000-0000-0000-0000-0000000000e0' $$,
  '23514',
  null,
  'Un ingreso no puede ser pago de tarjeta'
);

-- 7: B no ve las tarjetas de A
set local request.jwt.claims = '{"sub": "00000000-0000-0000-0000-0000000000b1", "role": "authenticated"}';
select is(
  (select count(*)::int from public.tarjetas) + (select count(*)::int from public.cuotas_tarjeta),
  0,
  'B no ve tarjetas ni cuotas de A'
);

select * from finish();
rollback;
