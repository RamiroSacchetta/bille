-- Tests de la moneda principal del perfil: solo pesos, reales, yenes o euros.
begin;
create extension if not exists pgtap with schema extensions;

select plan(3);

insert into auth.users (id, email, raw_user_meta_data)
values ('00000000-0000-0000-0000-0000000000c1', 'c1@ejemplo.com', '{"nombre": "Ana"}');

-- 1: el perfil nuevo arranca en pesos
select is(
  (select moneda_predeterminada::text from public.perfiles where id = '00000000-0000-0000-0000-0000000000c1'),
  'ARS',
  'El perfil nuevo arranca en pesos'
);

-- 2: se puede elegir reales
select lives_ok(
  $$ update public.perfiles set moneda_predeterminada = 'BRL' where id = '00000000-0000-0000-0000-0000000000c1' $$,
  'Se puede elegir reales como moneda principal'
);

-- 3: los dólares no son moneda principal (son un bolsillo aparte)
select throws_ok(
  $$ update public.perfiles set moneda_predeterminada = 'USD' where id = '00000000-0000-0000-0000-0000000000c1' $$,
  '23514',
  null,
  'Una moneda no soportada se rechaza'
);

select * from finish();
rollback;
