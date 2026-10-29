# Sprint 4 — Deploy en la nube

Dejar Bille listo para Supabase cloud + Render free (API) + Vercel (app), sin perder ni duplicar cargas aunque la API tarde.
Rama: `feat/sprint-4-deploy` (desde `main`) · Entrega: commits por unidad de trabajo · Tests: `pytest`, `ng test`, `supabase test db`.

## Specs

- **S1** — API despierta: "vamos con el cron que le pega a la api cada 10 mins, si veo que mis amigos no la usan, lo saco y listo". El cron lo configura el usuario (cron-job.org o UptimeRobot) contra `/api/salud`; se documenta en el README.
- **S2** — Del plan: "Guardar primero, enviar después": "toda carga se guarda en el dispositivo antes de enviarse y solo se borra cuando el servidor confirma; si se cierra la app esperando, se envía al volver a abrirla."
- **S3** — Del plan: "Identificador único por carga (idempotencia): el dispositivo genera un id; si el servidor lo recibe dos veces, devuelve lo ya guardado en lugar de duplicar. Aplica a gastos, ingresos y compras con tarjeta." También a los cambios de dólares, que se cargan igual.
- **S4** — Del plan: "Al abrir la app se despierta la API (pedido a `/api/salud`) y nunca se muestra el estado vacío mientras se carga." Si la API tarda, el service worker muestra los últimos datos (caché `freshness`), también con la API de la nube.
- **S5** — Del plan: "Ajustes de deploy: URLs por entorno (local vs nube) en el frontend; psycopg con `prepare_threshold=None` para el pooler de Supabase; verificar login con las claves de firma nuevas (JWKS, ya soportado); CORS solo para el dominio real; secretos en variables de entorno."
- **S6** — Pendientes del Sprint 3: "en `frontend/vercel.json`, poner en `connect-src` las URLs reales de la API y de Supabase ... uvicorn con `--proxy-headers`; "Confirm email" activado en la nube; activar Google en la nube".
  - Lo de código va en el repo.
  - Lo que se configura en los paneles queda en una guía paso a paso.
- **S7** — Del plan: "Cuentas en GitHub, Supabase, Vercel y Render las crea el usuario". La guía de deploy dice qué crear y qué valores copiar.

Supuestos:
- Las URLs reales de la nube no se conocen hasta que el usuario cree las cuentas. Por eso el entorno de producción y la CSP salen de valores que se completan en un solo lugar.
- Supabase URL y clave anónima son públicas por diseño.

## Tasks

| ID | Specs | Ruta | Estado | Commit |
|----|-------|------|--------|--------|
| T1 | S3 | inline | hecho | ver L2 |
| T2 | S2, S4 | inline | pendiente | |
| T3 | S5, S6 | inline | pendiente | |
| T4 | S1, S6, S7 | inline | pendiente | |

- T1: `id_carga` en movimientos y compras con tarjeta (base + backend): la segunda vez devuelve lo ya guardado.
- T2: frontend: toda carga pasa por la cola con su `id_carga`, se envía al abrir la app y al volver la red; ping a `/api/salud` al abrir; caché del service worker para la API de la nube.
- T3: config de nube: entorno de producción del frontend, CORS por variable, `prepare_threshold=None`, Render (`render.yaml` con `--proxy-headers`) y Vercel (build y CSP).
- T4: guía de deploy en el README: cuentas, variables, migraciones, cron, Confirm email, Google.

## Log

- **L1** (2026-10-29) "Sigamos entonces" (arrancar el Sprint 4). Ante el costo de la opción C (reescribir en SQL los cálculos de Python), el usuario eligió: "vamos con el cron que le pega a la api cada 10 mins, si veo que mis amigos no la usan, lo saco y listo". Después aclaró: "lo de guardar primero tiene que entrar tambien" (S2, T2).
- **L2** (2026-10-29) T1: `id_carga uuid`, único por usuario, en movimientos y compras con tarjeta.
  - Pasó de RED a GREEN en la base (pgTAP, 45 tests) y en el backend (112 tests, con un test contra Postgres).
  - El reenvío devuelve lo ya guardado, con 201, sin volver a validar el saldo.
  - Bloquea al usuario antes de buscar, para que dos reenvíos simultáneos no se dupliquen.
