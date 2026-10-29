-- Id de carga: lo genera el dispositivo para cada carga y lo manda con ella.
-- Si la misma carga llega dos veces (se cortó la red antes de la respuesta y la cola la reenvía),
-- el backend devuelve lo ya guardado en lugar de duplicarla. Es único por usuario.

alter table public.movimientos add column id_carga uuid;
create unique index movimientos_id_carga_idx on public.movimientos (usuario_id, id_carga)
  where id_carga is not null;

alter table public.compras_tarjeta add column id_carga uuid;
create unique index compras_tarjeta_id_carga_idx on public.compras_tarjeta (usuario_id, id_carga)
  where id_carga is not null;
