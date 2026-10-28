# Tarjetas de crédito

Seguir gastos con tarjeta de crédito (en cuotas) como deuda estimada; solo el pago real del resumen descuenta plata y cuenta como gasto.
Rama: `feat/tarjetas-credito` (desde `feat/sprint-1-mvp`) · Entrega: commits por unidad de trabajo · Tests: `pytest`, `supabase test db`, `ng test`.

## Specs

- **S1** — Registrar gastos con tarjeta y cuotas. "me gustaría agregar también que puedas seguir gastos de tarjeta de crédito" · "si pagaste algo en 3 cuotas, que lo puedas tener en algún lado".
- **S2** — Elegir la tarjeta y acumular. "podemos agregar un apartado que sea gasto con tarjeta de crédito y que pregunte con qué tarjeta de crédito lo gastó y que vaya acumulando".
- **S3** — Lo anotado es aproximado; el pago baja la deuda. "Lo que sea el resumen, digamos, sería un aproximado. Después, cuando el usuario ingrese, por ejemplo, pagué tanto de tanto tarjeta que se baje el total, digamos, de la deuda de la tarjeta, pero que no sea un dato de 100% verídico".
- **S4** — La compra no descuenta; el pago sí. "que cuando pongas gasto con tarjeta de crédito, digamos, no se te gaste de tu total, solamente los descuentes cuando vos anotás que pagaste el resumen de una tarjeta, que te descuente ese total. Y simplificamos todo".

Diseño acordado: en Carga rápida la tarjeta aparece en "Pagado con" y se eligen las cuotas; la compra no toca "Tu plata" ni "Gastos del mes"; el pago del resumen es un gasto (sale de plata del mes, ahorros o dividido) que baja la deuda estimada; si pagás menos, el resto queda pendiente.
Supuestos: cada cuota cae en el resumen según el día de cierre (compra hasta el día de cierre → resumen de ese mes; después → el siguiente); el resto de centavos de la división va en la primera cuota; la deuda estimada nunca se muestra negativa.

## Tasks

| ID | Specs | Ruta | Estado | Commit |
|----|-------|------|--------|--------|
| T1 | S1–S4 | inline | en curso | — |
| T2 | S1–S4 | inline | pendiente | — |
| T3 | S1–S4 | inline | pendiente | — |
| T4 | S1–S4 | inline | pendiente | — |
| T5 | S1–S4 | inline | pendiente | — |

- T1: migración (tarjetas, compras_tarjeta, cuotas_tarjeta, movimientos.tarjeta_id, RLS) + pgTAP.
- T2: dominio y casos de uso (cuotas, mes de resumen, deuda estimada, pago de resumen) + tests.
- T3: API y almacén Postgres + tests de API e integración.
- T4: frontend (tarjeta y cuotas en Carga rápida, pantalla Tarjetas, línea en Inicio) + tests.
- T5: prueba de punta a punta en el navegador.

Ruta: inline (unidades secuenciales).

## Log

- **L1** (2026-10-28) Pedido: "Antes de hacer el sprint 2, me gustaría agregar también que puedas seguir gastos de tarjeta de crédito. No sé cómo lo podríamos idear, pero por ejemplo, si pagaste algo en 3 cuotas, que lo puedas tener en algún lado."
- **L2** (2026-10-28) Diseño cerrado con S2–S4; el usuario aprobó: "Sí, implementalo".
