-- Moneda principal: cómo se muestra la plata que no es en dólares (pesos, reales, yenes o euros).
-- Solo cambia la presentación: los bolsillos y movimientos siguen guardados como 'ARS' y no se convierte nada.

alter table public.perfiles
  add constraint perfiles_moneda_predeterminada_check
  check (moneda_predeterminada in ('ARS', 'BRL', 'JPY', 'EUR'));
