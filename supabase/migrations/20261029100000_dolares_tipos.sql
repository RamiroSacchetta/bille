-- Dólares (1/2): valores nuevos de los enums.
-- Van en su propia migración porque Postgres no deja usar un valor de enum en la misma transacción que lo agrega.

alter type public.bolsillo add value if not exists 'dolares';
alter type public.tipo_movimiento add value if not exists 'cambio';
