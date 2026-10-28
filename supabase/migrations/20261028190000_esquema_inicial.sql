-- Esquema inicial de Bille (Sprint 1).
-- Modelo: la plata del usuario es una sola, repartida en bolsillos (disponible y ahorros).
-- Los objetivos son apartados dentro del bolsillo de ahorros.
-- Cada movimiento guarda su total y sus partes dicen de qué bolsillo u objetivo sale o entra la plata.

-- ---------------------------------------------------------------------------
-- Tipos
-- ---------------------------------------------------------------------------

create type public.tipo_movimiento as enum ('ingreso', 'gasto', 'transferencia');
create type public.bolsillo as enum ('disponible', 'ahorros');
create type public.origen_carga as enum ('manual');

-- ---------------------------------------------------------------------------
-- Tablas
-- ---------------------------------------------------------------------------

-- Un perfil por cada usuario de auth.users
create table public.perfiles (
  id uuid primary key references auth.users (id) on delete cascade,
  nombre_visible text not null check (length(nombre_visible) between 1 and 80),
  moneda_predeterminada char(3) not null default 'ARS',
  creado_en timestamptz not null default now()
);

create table public.metodos_pago (
  id uuid primary key default gen_random_uuid(),
  usuario_id uuid not null references public.perfiles (id) on delete cascade,
  nombre text not null check (length(nombre) between 1 and 60),
  tipo text not null check (tipo in ('efectivo', 'billetera', 'debito', 'credito', 'banco')),
  activo boolean not null default true,
  unique (usuario_id, nombre),
  -- Permite FKs compuestas que garantizan que el método sea del mismo usuario
  unique (id, usuario_id)
);

create table public.categorias (
  id uuid primary key default gen_random_uuid(),
  usuario_id uuid not null references public.perfiles (id) on delete cascade,
  nombre text not null check (length(nombre) between 1 and 60),
  tipo public.tipo_movimiento not null check (tipo in ('ingreso', 'gasto')),
  icono text,
  unique (usuario_id, nombre, tipo),
  unique (id, usuario_id)
);

-- Objetivos: apartados dentro del bolsillo de ahorros
create table public.objetivos (
  id uuid primary key default gen_random_uuid(),
  usuario_id uuid not null references public.perfiles (id) on delete cascade,
  nombre text not null check (length(nombre) between 1 and 80),
  monto_meta numeric(14, 2) not null check (monto_meta > 0),
  moneda char(3) not null default 'ARS',
  fecha_meta date,
  archivado boolean not null default false,
  creado_en timestamptz not null default now(),
  unique (id, usuario_id)
);
create index objetivos_usuario_idx on public.objetivos (usuario_id);

-- Un renglón por hecho: lo que el usuario ve en su lista de movimientos
create table public.movimientos (
  id uuid primary key default gen_random_uuid(),
  usuario_id uuid not null references public.perfiles (id) on delete cascade,
  tipo public.tipo_movimiento not null,
  monto numeric(14, 2) not null check (monto > 0),
  moneda char(3) not null default 'ARS',
  ocurrido_en timestamptz not null,
  descripcion text check (length(descripcion) <= 200),
  categoria_id uuid,
  metodo_pago_id uuid,
  origen public.origen_carga not null default 'manual',
  id_externo text,
  creado_en timestamptz not null default now(),
  unique (usuario_id, origen, id_externo),
  unique (id, usuario_id),
  -- Al borrar una categoría o método solo se limpia esa columna, no usuario_id
  foreign key (categoria_id, usuario_id)
    references public.categorias (id, usuario_id) on delete set null (categoria_id),
  foreign key (metodo_pago_id, usuario_id)
    references public.metodos_pago (id, usuario_id) on delete set null (metodo_pago_id),
  -- Las transferencias no llevan categoría
  check (tipo <> 'transferencia' or categoria_id is null)
);
create index movimientos_usuario_fecha_idx on public.movimientos (usuario_id, ocurrido_en desc);
create index movimientos_categoria_idx on public.movimientos (categoria_id) where categoria_id is not null;
create index movimientos_metodo_pago_idx on public.movimientos (metodo_pago_id) where metodo_pago_id is not null;

-- Partes de un movimiento: de qué bolsillo (y objetivo) sale o entra cada monto.
-- Monto con signo: positivo entra, negativo sale.
create table public.partes_movimiento (
  id uuid primary key default gen_random_uuid(),
  movimiento_id uuid not null,
  usuario_id uuid not null,
  bolsillo public.bolsillo not null,
  objetivo_id uuid,
  monto numeric(14, 2) not null check (monto <> 0),
  foreign key (movimiento_id, usuario_id)
    references public.movimientos (id, usuario_id) on delete cascade,
  foreign key (objetivo_id, usuario_id)
    references public.objetivos (id, usuario_id) on delete restrict,
  -- Un objetivo solo existe dentro de ahorros
  check (objetivo_id is null or bolsillo = 'ahorros')
);
create index partes_movimiento_movimiento_idx on public.partes_movimiento (movimiento_id);
create index partes_movimiento_usuario_idx on public.partes_movimiento (usuario_id, bolsillo);
create index partes_movimiento_objetivo_idx on public.partes_movimiento (objetivo_id) where objetivo_id is not null;

-- ---------------------------------------------------------------------------
-- Cuadre de partes: se valida al final de la transacción
--   ingreso:       partes positivas que suman +monto
--   gasto:         partes negativas que suman -monto
--   transferencia: al menos dos partes que suman 0
-- ---------------------------------------------------------------------------

create schema if not exists privado;
revoke all on schema privado from public, anon, authenticated;

create or replace function privado.validar_cuadre(p_movimiento_id uuid)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_tipo public.tipo_movimiento;
  v_monto numeric(14, 2);
  v_suma numeric(14, 2);
  v_cantidad int;
  v_positivas int;
  v_negativas int;
begin
  select tipo, monto into v_tipo, v_monto
  from public.movimientos
  where id = p_movimiento_id;

  -- El movimiento fue borrado: sus partes se fueron en cascada
  if not found then
    return;
  end if;

  select coalesce(sum(monto), 0),
         count(*),
         count(*) filter (where monto > 0),
         count(*) filter (where monto < 0)
    into v_suma, v_cantidad, v_positivas, v_negativas
  from public.partes_movimiento
  where movimiento_id = p_movimiento_id;

  if v_cantidad = 0 then
    raise exception 'El movimiento % no tiene partes', p_movimiento_id
      using errcode = 'check_violation';
  end if;

  if v_tipo = 'ingreso' and (v_negativas > 0 or v_suma <> v_monto) then
    raise exception 'Las partes del ingreso % deben ser positivas y sumar %', p_movimiento_id, v_monto
      using errcode = 'check_violation';
  elsif v_tipo = 'gasto' and (v_positivas > 0 or v_suma <> -v_monto) then
    raise exception 'Las partes del gasto % deben ser negativas y sumar -%', p_movimiento_id, v_monto
      using errcode = 'check_violation';
  elsif v_tipo = 'transferencia' and (v_cantidad < 2 or v_suma <> 0 or v_positivas = 0) then
    raise exception 'Las partes de la transferencia % deben sumar 0', p_movimiento_id
      using errcode = 'check_violation';
  end if;
end;
$$;

create or replace function privado.tr_cuadre_partes()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if tg_op in ('UPDATE', 'DELETE') then
    perform privado.validar_cuadre(old.movimiento_id);
  end if;
  if tg_op in ('INSERT', 'UPDATE') then
    perform privado.validar_cuadre(new.movimiento_id);
  end if;
  return null;
end;
$$;

create or replace function privado.tr_cuadre_movimiento()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  perform privado.validar_cuadre(new.id);
  return null;
end;
$$;

create constraint trigger cuadre_partes
  after insert or update or delete on public.partes_movimiento
  deferrable initially deferred
  for each row execute function privado.tr_cuadre_partes();

create constraint trigger cuadre_movimiento
  after insert or update of tipo, monto on public.movimientos
  deferrable initially deferred
  for each row execute function privado.tr_cuadre_movimiento();

-- ---------------------------------------------------------------------------
-- Saldos (vistas con security_invoker para que apliquen las políticas RLS)
-- ---------------------------------------------------------------------------

create view public.saldos_bolsillos
with (security_invoker = true) as
select
  p.id as usuario_id,
  coalesce(sum(pm.monto) filter (where pm.bolsillo = 'disponible'), 0)::numeric(14, 2) as disponible,
  coalesce(sum(pm.monto) filter (where pm.bolsillo = 'ahorros'), 0)::numeric(14, 2) as ahorros,
  coalesce(sum(pm.monto) filter (where pm.objetivo_id is not null), 0)::numeric(14, 2) as apartado
from public.perfiles p
left join public.partes_movimiento pm on pm.usuario_id = p.id
group by p.id;

create view public.saldos_objetivos
with (security_invoker = true) as
select
  o.id as objetivo_id,
  o.usuario_id,
  coalesce(sum(pm.monto), 0)::numeric(14, 2) as apartado
from public.objetivos o
left join public.partes_movimiento pm on pm.objetivo_id = o.id
group by o.id, o.usuario_id;

-- ---------------------------------------------------------------------------
-- Alta automática del perfil con categorías y métodos de pago por defecto
-- ---------------------------------------------------------------------------

create or replace function privado.crear_perfil_inicial()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into public.perfiles (id, nombre_visible)
  values (
    new.id,
    coalesce(nullif(trim(new.raw_user_meta_data ->> 'nombre'), ''), split_part(new.email, '@', 1))
  );

  insert into public.categorias (usuario_id, nombre, tipo, icono)
  values
    (new.id, 'Supermercado', 'gasto', 'carrito'),
    (new.id, 'Salidas', 'gasto', 'taza'),
    (new.id, 'Transporte', 'gasto', 'colectivo'),
    (new.id, 'Auto', 'gasto', 'auto'),
    (new.id, 'Hogar', 'gasto', 'casa'),
    (new.id, 'Salud', 'gasto', 'salud'),
    (new.id, 'Ocio', 'gasto', 'ocio'),
    (new.id, 'Sueldo', 'ingreso', 'sueldo'),
    (new.id, 'Freelance', 'ingreso', 'freelance'),
    (new.id, 'Regalo', 'ingreso', 'regalo'),
    (new.id, 'Otros', 'ingreso', 'otros');

  insert into public.metodos_pago (usuario_id, nombre, tipo)
  values
    (new.id, 'Efectivo', 'efectivo'),
    (new.id, 'Débito', 'debito'),
    (new.id, 'Mercado Pago', 'billetera'),
    (new.id, 'Banco', 'banco');

  return new;
end;
$$;

revoke execute on function privado.crear_perfil_inicial() from public, anon, authenticated;

create trigger al_crear_usuario
  after insert on auth.users
  for each row execute function privado.crear_perfil_inicial();

-- ---------------------------------------------------------------------------
-- Seguridad: RLS en todas las tablas, cada usuario ve solo lo suyo
-- ---------------------------------------------------------------------------

alter table public.perfiles enable row level security;
alter table public.metodos_pago enable row level security;
alter table public.categorias enable row level security;
alter table public.objetivos enable row level security;
alter table public.movimientos enable row level security;
alter table public.partes_movimiento enable row level security;

create policy perfiles_propios on public.perfiles
  for all to authenticated
  using (id = (select auth.uid()))
  with check (id = (select auth.uid()));

create policy metodos_pago_propios on public.metodos_pago
  for all to authenticated
  using (usuario_id = (select auth.uid()))
  with check (usuario_id = (select auth.uid()));

create policy categorias_propias on public.categorias
  for all to authenticated
  using (usuario_id = (select auth.uid()))
  with check (usuario_id = (select auth.uid()));

create policy objetivos_propios on public.objetivos
  for all to authenticated
  using (usuario_id = (select auth.uid()))
  with check (usuario_id = (select auth.uid()));

create policy movimientos_propios on public.movimientos
  for all to authenticated
  using (usuario_id = (select auth.uid()))
  with check (usuario_id = (select auth.uid()));

create policy partes_movimiento_propias on public.partes_movimiento
  for all to authenticated
  using (usuario_id = (select auth.uid()))
  with check (usuario_id = (select auth.uid()));

-- El rol anónimo no accede a nada; el perfil no se crea ni se borra desde la app
revoke all on all tables in schema public from anon;
revoke insert, delete on public.perfiles from authenticated;

-- Las funciones de validación las usan solo los triggers
revoke execute on all functions in schema privado from public, anon, authenticated;
