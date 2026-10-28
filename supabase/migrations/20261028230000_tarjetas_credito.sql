-- Tarjetas de crédito.
-- Las compras con tarjeta NO mueven plata: se acumulan como deuda estimada, repartida en cuotas por resumen.
-- Solo el pago del resumen (un movimiento de tipo gasto con tarjeta_id) descuenta plata y cuenta como gasto del mes.

create table public.tarjetas (
  id uuid primary key default gen_random_uuid(),
  usuario_id uuid not null references public.perfiles (id) on delete cascade,
  nombre text not null check (length(nombre) between 1 and 60),
  dia_cierre smallint not null check (dia_cierre between 1 and 31),
  dia_vencimiento smallint not null check (dia_vencimiento between 1 and 31),
  activa boolean not null default true,
  creado_en timestamptz not null default now(),
  unique (usuario_id, nombre),
  unique (id, usuario_id)
);

-- Una compra con tarjeta: el total y en cuántas cuotas se paga
create table public.compras_tarjeta (
  id uuid primary key default gen_random_uuid(),
  usuario_id uuid not null,
  tarjeta_id uuid not null,
  descripcion text check (length(descripcion) <= 200),
  categoria_id uuid,
  monto_total numeric(14, 2) not null check (monto_total > 0),
  cantidad_cuotas smallint not null check (cantidad_cuotas between 1 and 60),
  comprado_en date not null,
  creado_en timestamptz not null default now(),
  unique (id, usuario_id),
  foreign key (tarjeta_id, usuario_id) references public.tarjetas (id, usuario_id) on delete cascade,
  foreign key (categoria_id, usuario_id)
    references public.categorias (id, usuario_id) on delete set null (categoria_id)
);
create index compras_tarjeta_tarjeta_idx on public.compras_tarjeta (tarjeta_id, comprado_en desc);
create index compras_tarjeta_usuario_idx on public.compras_tarjeta (usuario_id);
create index compras_tarjeta_categoria_idx on public.compras_tarjeta (categoria_id) where categoria_id is not null;

-- Cada cuota cae en el resumen de un mes (primer día del mes en que cierra ese resumen)
create table public.cuotas_tarjeta (
  id uuid primary key default gen_random_uuid(),
  compra_id uuid not null,
  usuario_id uuid not null,
  tarjeta_id uuid not null,
  numero smallint not null check (numero >= 1),
  monto numeric(14, 2) not null check (monto > 0),
  mes_resumen date not null check (extract(day from mes_resumen) = 1),
  unique (compra_id, numero),
  foreign key (compra_id, usuario_id) references public.compras_tarjeta (id, usuario_id) on delete cascade,
  foreign key (tarjeta_id, usuario_id) references public.tarjetas (id, usuario_id) on delete cascade
);
create index cuotas_tarjeta_tarjeta_mes_idx on public.cuotas_tarjeta (tarjeta_id, mes_resumen);
create index cuotas_tarjeta_usuario_idx on public.cuotas_tarjeta (usuario_id);

-- El pago de un resumen es un gasto que apunta a la tarjeta pagada
alter table public.movimientos add column tarjeta_id uuid;
alter table public.movimientos
  add constraint movimientos_tarjeta_fk foreign key (tarjeta_id, usuario_id)
    references public.tarjetas (id, usuario_id) on delete set null (tarjeta_id),
  add constraint movimientos_tarjeta_solo_gasto check (tarjeta_id is null or tipo = 'gasto');
create index movimientos_tarjeta_idx on public.movimientos (tarjeta_id) where tarjeta_id is not null;

-- Deuda estimada por tarjeta: lo anotado en cuotas menos lo pagado (nunca negativa)
create view public.deudas_tarjetas
with (security_invoker = true) as
select
  t.id as tarjeta_id,
  t.usuario_id,
  coalesce((select sum(c.monto) from public.cuotas_tarjeta c where c.tarjeta_id = t.id), 0)::numeric(14, 2) as anotado,
  coalesce((select sum(m.monto) from public.movimientos m where m.tarjeta_id = t.id), 0)::numeric(14, 2) as pagado,
  greatest(
    coalesce((select sum(c.monto) from public.cuotas_tarjeta c where c.tarjeta_id = t.id), 0)
      - coalesce((select sum(m.monto) from public.movimientos m where m.tarjeta_id = t.id), 0),
    0
  )::numeric(14, 2) as deuda_estimada
from public.tarjetas t;

-- Seguridad: cada usuario ve solo lo suyo
alter table public.tarjetas enable row level security;
alter table public.compras_tarjeta enable row level security;
alter table public.cuotas_tarjeta enable row level security;

create policy tarjetas_propias on public.tarjetas
  for all to authenticated
  using (usuario_id = (select auth.uid()))
  with check (usuario_id = (select auth.uid()));

create policy compras_tarjeta_propias on public.compras_tarjeta
  for all to authenticated
  using (usuario_id = (select auth.uid()))
  with check (usuario_id = (select auth.uid()));

create policy cuotas_tarjeta_propias on public.cuotas_tarjeta
  for all to authenticated
  using (usuario_id = (select auth.uid()))
  with check (usuario_id = (select auth.uid()));

revoke all on public.tarjetas, public.compras_tarjeta, public.cuotas_tarjeta, public.deudas_tarjetas from anon;
