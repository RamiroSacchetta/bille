-- Cuentas creadas con Google: el perfil toma el nombre de pila de `full_name`
-- (Google no manda el campo `nombre` que usa el registro con email).

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
    left(coalesce(
      nullif(trim(new.raw_user_meta_data ->> 'nombre'), ''),
      nullif(split_part(trim(new.raw_user_meta_data ->> 'full_name'), ' ', 1), ''),
      split_part(new.email, '@', 1)
    ), 80)
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
