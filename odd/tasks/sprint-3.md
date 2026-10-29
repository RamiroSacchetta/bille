# Sprint 3 — Seguridad y acceso

Lo necesario para salir a internet con pocos amigos invitados, todo configurado y probado en local.
Rama: `feat/sprint-3-seguridad` (desde `feat/sprint-2-calidad`) · Entrega: commits por unidad de trabajo · Tests: `pytest`, `ng test`, `supabase test db`.

## Specs

- **S1** — Del plan: "Entrar con Google (OAuth de Supabase) además de email y contraseña. El cliente OAuth en Google Cloud lo crea el usuario."
- **S2** — Del plan: "Registro solo por invitación: lista de emails permitidos, aplicada también a Google."
- **S3** — Del plan: "Contraseñas: mínimo 8 caracteres". El bloqueo de contraseñas filtradas queda afuera: "No hagamos lo de las contrasenas filtradas".
- **S4** — Del plan: "Configuración segura: el backend no arranca fuera de desarrollo si faltan variables de entorno (nada de secretos por defecto)."
- **S5** — Del plan: "Límite de pedidos por minuto en la API (fuerza bruta y abuso)."
- **S6** — Del plan: "Encabezados de seguridad (CSP, HSTS, etc.) preparados para Vercel."
- **S7** — Del plan: "Dependencias: avisos automáticos de vulnerabilidades (Dependabot) al subir a GitHub."
- **S8** — Del plan: "Backups propios: script de copia periódica de la base."

Supuestos: además del mínimo de 8 se exigen letras y números (`letters_digits`, gratis en Supabase); la lista de invitados es una tabla que se edita por SQL o desde Supabase Studio, controlada por el hook `before_user_created` de Supabase Auth; el límite de pedidos es en memoria por usuario (o IP sin sesión), suficiente para una sola instancia en Render.

## Tasks

| ID | Specs | Ruta | Estado | Commit |
|----|-------|------|--------|--------|
| T1 | S3 | inline | pendiente | — |
| T2 | S2 | inline | pendiente | — |
| T3 | S1 | inline | pendiente | — |
| T4 | S4 | inline | pendiente | — |
| T5 | S5 | inline | pendiente | — |
| T6 | S6, S7 | inline | pendiente | — |
| T7 | S8 | inline | pendiente | — |

- T1: `minimum_password_length = 8` y `letters_digits` en Supabase; validación y mensajes en la pantalla de ingreso.
- T2: tabla `invitaciones`, función hook que rechaza emails no invitados, configuración del hook y test pgTAP.
- T3: proveedor Google en `config.toml` con secretos por variable de entorno; botón "Continuar con Google".
- T4: variable `entorno`; fuera de `desarrollo` exige URL de base, URL de Supabase y secreto JWT.
- T5: límite de pedidos por minuto con respuesta 429.
- T6: `frontend/vercel.json` con encabezados de seguridad y `.github/dependabot.yml`.
- T7: script de backup de la base con `pg_dump` y rotación.

## Log

- **L1** (2026-10-28) El usuario pidió "Arranquemos con el sprint 3".
- **L2** (2026-10-28) El bloqueo de contraseñas filtradas de Supabase es del plan Pro (no gratis) y no se configura en local. Ante la consulta, el usuario respondió "No hagamos lo de las contrasenas filtradas".
