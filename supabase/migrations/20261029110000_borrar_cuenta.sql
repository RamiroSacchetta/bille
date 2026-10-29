-- Borrar una cuenta con plata apartada en objetivos fallaba: al borrar el perfil, la cascada borra objetivos y
-- movimientos, pero la FK de partes → objetivos se chequeaba antes de que la cascada borrara las partes.
-- Ahora es diferible: se chequea al final de la transacción, cuando ya no queda nada de la cuenta.
-- Un objetivo con movimientos sigue sin poder borrarse por sí solo.

alter table public.partes_movimiento
  drop constraint partes_movimiento_objetivo_id_usuario_id_fkey,
  add constraint partes_movimiento_objetivo_id_usuario_id_fkey
    foreign key (objetivo_id, usuario_id) references public.objetivos (id, usuario_id)
    on delete no action deferrable initially deferred;
