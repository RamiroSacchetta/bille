-- Registro solo por invitación: Supabase Auth llama a este hook antes de crear cada usuario
-- (email y contraseña o Google) y rechaza los emails que no están en la lista.
-- Para invitar a alguien: insert into public.invitaciones (email) values ('amiga@ejemplo.com');

create table public.invitaciones (
  email text primary key check (email = lower(email)),
  creado_en timestamptz not null default now()
);

comment on table public.invitaciones is 'Emails que pueden crear una cuenta en Bille. Se edita por SQL o desde Studio.';

-- Normaliza a minúsculas para que la comparación no dependa de cómo se escribió
create function public.normalizar_invitacion()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.email := lower(trim(new.email));
  return new;
end;
$$;

create trigger invitaciones_normalizar
before insert or update on public.invitaciones
for each row execute function public.normalizar_invitacion();

-- Nadie de la app la ve: solo el servicio de Auth la lee
alter table public.invitaciones enable row level security;
revoke all on table public.invitaciones from anon, authenticated, public;
grant select on table public.invitaciones to supabase_auth_admin;

create policy "auth lee las invitaciones"
on public.invitaciones for select
to supabase_auth_admin
using (true);

create function public.hook_antes_de_crear_usuario(event jsonb)
returns jsonb
language plpgsql
stable
set search_path = ''
as $$
declare
  correo text := lower(trim(event -> 'user' ->> 'email'));
begin
  if correo is not null and exists (select 1 from public.invitaciones where email = correo) then
    return '{}'::jsonb;
  end if;
  return jsonb_build_object(
    'error', jsonb_build_object(
      'http_code', 403,
      'message', 'Bille es solo por invitación. Pedile a quien te la recomendó que te invite.'
    )
  );
end;
$$;

grant execute on function public.hook_antes_de_crear_usuario(jsonb) to supabase_auth_admin;
revoke execute on function public.hook_antes_de_crear_usuario(jsonb) from anon, authenticated, public;
revoke execute on function public.normalizar_invitacion() from anon, authenticated, public;
