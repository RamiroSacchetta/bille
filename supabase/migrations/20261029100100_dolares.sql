-- Dólares (2/2): un bolsillo en dólares, objetivos con moneda y el cambio entre pesos y dólares.
-- Los dólares nunca se convierten: cada parte está en la moneda de su bolsillo (dolares → USD, el resto → ARS).
-- Un cambio tiene una parte en pesos y otra en dólares con signos opuestos; su monto son los dólares.

-- ---------------------------------------------------------------------------
-- Restricciones
-- ---------------------------------------------------------------------------

alter table public.objetivos
  add constraint objetivos_moneda_check check (moneda in ('ARS', 'USD'));

alter table public.movimientos
  add constraint movimientos_moneda_check check (moneda in ('ARS', 'USD')),
  add constraint movimientos_cambio_sin_categoria check (tipo <> 'cambio' or categoria_id is null),
  add constraint movimientos_tarjeta_en_pesos check (tarjeta_id is null or moneda = 'ARS');

-- Un objetivo vive dentro de ahorros (pesos) o de dólares
alter table public.partes_movimiento
  drop constraint partes_movimiento_check,
  add constraint partes_movimiento_objetivo_en_ahorro check (objetivo_id is null or bolsillo in ('ahorros', 'dolares'));

-- ---------------------------------------------------------------------------
-- Cuadre de partes
--   ingreso:       partes positivas que suman +monto
--   gasto:         partes negativas que suman -monto
--   transferencia: al menos dos partes que suman 0
--   cambio:        una parte en dólares de ±monto y otra en pesos con el signo opuesto
-- Fuera del cambio, todas las partes están en la moneda del movimiento.
-- Una parte en un objetivo tiene que estar en la moneda del objetivo.
-- ---------------------------------------------------------------------------

create or replace function privado.validar_cuadre(p_movimiento_id uuid)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_tipo public.tipo_movimiento;
  v_monto numeric(14, 2);
  v_moneda char(3);
  v_suma numeric(14, 2);
  v_cantidad int;
  v_positivas int;
  v_negativas int;
  v_partes_usd int;
  v_suma_usd numeric(14, 2);
  v_partes_ars int;
  v_suma_ars numeric(14, 2);
begin
  select tipo, monto, moneda into v_tipo, v_monto, v_moneda
  from public.movimientos
  where id = p_movimiento_id;

  -- El movimiento fue borrado: sus partes se fueron en cascada
  if not found then
    return;
  end if;

  select coalesce(sum(monto), 0),
         count(*),
         count(*) filter (where monto > 0),
         count(*) filter (where monto < 0),
         count(*) filter (where bolsillo = 'dolares'),
         coalesce(sum(monto) filter (where bolsillo = 'dolares'), 0),
         count(*) filter (where bolsillo <> 'dolares'),
         coalesce(sum(monto) filter (where bolsillo <> 'dolares'), 0)
    into v_suma, v_cantidad, v_positivas, v_negativas, v_partes_usd, v_suma_usd, v_partes_ars, v_suma_ars
  from public.partes_movimiento
  where movimiento_id = p_movimiento_id;

  if v_cantidad = 0 then
    raise exception 'El movimiento % no tiene partes', p_movimiento_id
      using errcode = 'check_violation';
  end if;

  if exists (
    select 1
    from public.partes_movimiento pm
    join public.objetivos o on o.id = pm.objetivo_id
    where pm.movimiento_id = p_movimiento_id
      and o.moneda <> case when pm.bolsillo = 'dolares' then 'USD' else 'ARS' end
  ) then
    raise exception 'Una parte del movimiento % no está en la moneda de su objetivo', p_movimiento_id
      using errcode = 'check_violation';
  end if;

  if v_tipo = 'cambio' then
    if v_moneda <> 'USD' or v_partes_usd <> 1 or v_partes_ars <> 1
       or abs(v_suma_usd) <> v_monto or sign(v_suma_usd) = sign(v_suma_ars) then
      raise exception 'El cambio % necesita una parte en dólares por % y otra en pesos con el signo opuesto',
        p_movimiento_id, v_monto
        using errcode = 'check_violation';
    end if;
    return;
  end if;

  if (v_moneda = 'USD' and v_partes_ars > 0) or (v_moneda = 'ARS' and v_partes_usd > 0) then
    raise exception 'Las partes del movimiento % tienen que estar en %', p_movimiento_id, v_moneda
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

revoke execute on function privado.validar_cuadre(uuid) from public, anon, authenticated;

-- Cambiar la moneda de un movimiento también tiene que volver a validar el cuadre
drop trigger cuadre_movimiento on public.movimientos;
create constraint trigger cuadre_movimiento
  after insert or update of tipo, monto, moneda on public.movimientos
  deferrable initially deferred
  for each row execute function privado.tr_cuadre_movimiento();

-- ---------------------------------------------------------------------------
-- Saldos: lo apartado en pesos y en dólares por separado
-- ---------------------------------------------------------------------------

create or replace view public.saldos_bolsillos
with (security_invoker = true) as
select
  p.id as usuario_id,
  coalesce(sum(pm.monto) filter (where pm.bolsillo = 'disponible'), 0)::numeric(14, 2) as disponible,
  coalesce(sum(pm.monto) filter (where pm.bolsillo = 'ahorros'), 0)::numeric(14, 2) as ahorros,
  coalesce(sum(pm.monto) filter (where pm.bolsillo = 'ahorros' and pm.objetivo_id is not null), 0)::numeric(14, 2)
    as apartado,
  coalesce(sum(pm.monto) filter (where pm.bolsillo = 'dolares'), 0)::numeric(14, 2) as dolares,
  coalesce(sum(pm.monto) filter (where pm.bolsillo = 'dolares' and pm.objetivo_id is not null), 0)::numeric(14, 2)
    as apartado_dolares
from public.perfiles p
left join public.partes_movimiento pm on pm.usuario_id = p.id
group by p.id;
