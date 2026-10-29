# Dólares

Ahorro, gasto y objetivos en dólares, siempre separados de los pesos (sin cotización en el total).
Rama: `feat/dolares` (desde `feat/sprint-3-seguridad`) · Entrega: commits por unidad de trabajo · Tests: `pytest`, `ng test`, `supabase test db`.

## Specs

- **S1** — Dólares separados de los pesos: "Yo creo que separados, como un ahorro casi nadie tiene dólares y los usa para la vida cotidiana". El total en pesos, los ingresos y los gastos del mes no incluyen dólares ni usan ninguna cotización.
- **S2** — Comprar dólares con pesos: "elegir de dónde se sacan si de la plata que tenés disponible". Es un cambio, no un gasto: salen pesos (de disponible o de ahorros) y entran dólares; el movimiento guarda los dos montos.
- **S3** — Dólares que ya tenías: "o los tenías abajo del colchón digamos". Entran a dólares sin contar como ingreso del mes en pesos.
- **S4** — Vender dólares: "puede pasar que alguien se quede sin plata 1 mes y cambie 100 o 200 para hacer algo". Salen dólares y entran pesos a disponible; no cuenta como ingreso del mes.
- **S5** — "Quiero poder gastar o generar un objetivo en dólares, por ejemplo un viaje". Objetivos con moneda (pesos o dólares); los de dólares se apartan desde los dólares. Un gasto se carga en una sola moneda; en dólares sale de dólares libres y/o de objetivos en dólares.
- **S6** — Ningún saldo puede quedar negativo, en ninguna de las dos monedas.
- **S7** — Pantallas: inicio con los dólares (total y libres) y los objetivos con su moneda; "Gastos en dólares US$ X" aparte cuando hubo gastos en dólares en el mes; carga de comprar, vender, "ya los tenía" y gastos en dólares; la lista de movimientos y el CSV muestran la moneda.

Fuera de alcance: tarjetas de crédito en dólares, cotización automática.

- **S8** — Contrato de la API (decisión técnica para hacer backend y frontend en paralelo):
  - Bolsillos: `disponible`, `ahorros` (pesos) y `dolares` (dólares). Los objetivos en pesos viven en `ahorros` y los objetivos en dólares en `dolares`. Moneda: `"ARS"` o `"USD"`.
  - `GET /api/resumen`: `saldos` suma `dolares` y `dolares_libres` (string, lo no apartado); `total` sigue siendo `disponible + ahorros` (solo pesos). Se suma `gastos_dolares_mes` (string). `ingresos_mes` y `gastos_mes` cuentan solo movimientos en pesos. Cada objetivo trae `moneda`.
  - `GET /api/objetivos` y `POST /api/objetivos`: el objetivo tiene `moneda` (`"ARS"` por defecto al crear).
  - Movimiento (salida): suma `moneda`. `tipo` puede ser `"cambio"`. En un cambio, `monto` son los dólares y `moneda` es `"USD"`. Tiene dos partes: una en `dolares` (positiva si compraste y negativa si vendiste) y otra en pesos con signo opuesto, cuyo valor absoluto son los pesos.
  - `POST /api/movimientos/cambios` → 201 Movimiento. Cuerpo: `{operacion: "compra" | "venta", dolares, pesos, ocurrido_en, pesos_en?: {bolsillo: "disponible" | "ahorros"}, descripcion?}`.
    - `pesos_en` es de dónde salen los pesos en una compra y adónde entran en una venta; por defecto `disponible`.
    - Los dólares entran o salen de los dólares libres.
  - `POST /api/movimientos/ingresos` con `destino: {bolsillo: "dolares"}` es un ingreso en dólares ("ya los tenía"): `moneda` es `"USD"` y no cuenta en `ingresos_mes`.
  - `POST /api/movimientos/gastos` con orígenes en `dolares` (libres o un objetivo en dólares) es un gasto en dólares: cuenta en `gastos_dolares_mes`, no en `gastos_mes`. Si mezcla monedas → 422 "Un gasto va en una sola moneda". Sin orígenes sale de `disponible`, en pesos.
  - `POST /api/movimientos/transferencias` solo dentro de la misma moneda; sirve para apartar o devolver en un objetivo en dólares. Si mezcla monedas → 422 "Para pasar entre pesos y dólares usá Comprar o Vender dólares".
  - Un objetivo solo acepta partes de su moneda → 422 "El objetivo es en otra moneda".
  - Saldo negativo de dólares → 409 "No te alcanzan los dólares libres para este movimiento" o "No te alcanza lo apartado en el objetivo para este movimiento".

## Tasks

| ID | Specs | Ruta | Estado | Commit |
|----|-------|------|--------|--------|
| T1 | S1–S6 | inline | hecho | 8832797 |
| T2 | S1–S6, S8 | inline | hecho | 4538728 |
| T3 | S7, S8 | delegada (paralelo con T1–T2, superficies disjuntas) | en curso | |

- T1: base de datos: bolsillo `dolares`, moneda en objetivos, tipo `cambio`, validaciones y saldos; tests pgTAP.
- T2: backend: dominio, casos de uso, almacén y API; tests.
- T3: frontend: carga, inicio, ahorros, movimientos y CSV; tests.

## Log

- **L1** (2026-10-29) Pedido original: "Ok, agreguemos lo de los dolares, contame cómo pensas implementarlo ?" → "Quiero poder gastar o generar un objetivo en dólares, por ejemplo un viaje" → "Arranca con eso y cuando termines reinicia el backend así puedo verlo de mi celular".
- **L2** (2026-10-29) T1:
  - Las migraciones van en dos archivos, porque un valor de enum nuevo no se puede usar en la misma transacción que lo agrega.
  - Se aplicaron con `supabase migration up` (sin reset, para no borrar los datos locales).
  - pgTAP pasó de RED a GREEN: 38 tests.
- **L3** (2026-10-29) T2:
  - RED (falla al importar) → GREEN. Backend: 103 tests, contando el flujo de dólares de punta a punta contra Postgres; ruff limpio.
  - Se mantuvo el mensaje de siempre para un objetivo en disponible.
  - El CSV suma la columna "Moneda".
  - El cambio tiene sus partes ordenadas: primero sale y después entra.
