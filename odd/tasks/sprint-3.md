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
| T1 | S3 | inline | hecho | 02fd771 |
| T2 | S2 | inline | hecho | 0f5873c |
| T3 | S1 | inline | hecho (falta el cliente de Google del usuario) | 38b8294 |
| T4 | S4 | inline | hecho | e88e13e |
| T5 | S5 | inline | hecho | ac77906 |
| T6 | S6, S7 | inline | hecho | 4af29dd |
| T7 | S8 | inline | hecho (script sin correr por la herramienta, ver L8) | f52e77d |

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
- **L3** (2026-10-28) T1: RED (módulo inexistente) → GREEN, frontend 25/25. Supabase local reiniciado: `abc12` → "Password should be at least 8 characters."; `solamenteletras` → "Password should contain at least one character of each...". Las cuentas existentes con contraseñas de 6 siguen entrando (la regla solo se valida al crear la cuenta).
- **L4** (2026-10-28) T2: pgTAP RED → GREEN (24 tests de base). Integración: signup sin invitación → 403 "Bille es solo por invitación..."; los tests de integración ahora invitan el email antes de registrarse. Backend 64.
- **L5** (2026-10-28) T3: pgTAP RED ("lucia" en vez de "Lucía") → GREEN (27). Con Google activado y un cliente de prueba: `/auth/v1/settings` → `google:true` y `/authorize?provider=google` → 302 a accounts.google.com con `redirect_uri=http://127.0.0.1:54321/auth/v1/callback`. En el navegador se ven el botón y el error de invitación al volver. Queda `enabled = false` hasta que el usuario cree el cliente OAuth. Frontend 28/28.
- **L6** (2026-10-28) T4: RED 4/5 → GREEN; `ENTORNO=produccion` sin variables → "Faltan variables de entorno: URL_BASE_DATOS, SUPABASE_URL, SUPABASE_JWT_SECRET". Backend 69. T5: RED → GREEN, backend 73, ruff limpio.
- **L7** (2026-10-28) T6: el build ponía `onload` en línea para los estilos, que la CSP bloquearía: se desactivó `inlineCritical`. Build servido con los encabezados: sin violaciones de CSP, con estilos y fuente aplicados. En el navegador integrado, con el service worker activo, los pedidos a `127.0.0.1:54321` dan 504 con o sin CSP (no lo causa este cambio; ya en L3 del Sprint 2 el panel bloqueaba ese puerto). Conviene confirmarlo en Edge en :8080.
- **L8** (2026-10-28) T7: la herramienta no permitió correr `backup.ps1` con `-ExecutionPolicy Bypass`. Se probaron los tres `supabase db dump --local` del script: roles 370 B, esquema 29 KB, datos 194 KB con `auth.users`, `invitaciones`, `perfiles` y `movimientos`. Falta que el usuario corra el script.
- **L9** (2026-10-28) Verificador independiente: sin blockers. S2–S8 cumplen; S1 parcial como estaba previsto. Se corrigieron en una tanda (RED → GREEN): A1, porque el secreto local se rechaza siempre que Supabase no sea local, aunque falte ENTORNO; A2, porque las variables vacías cuentan como faltantes; A5, porque solo cuentan letras a-z/A-Z, como en Supabase; A7, que agrega `/**` a las URLs de retorno; A6, porque los tests de integración ahora borran sus cuentas e invitaciones. A3 y A4 quedaron en el README; A8, A9 y la FK sin cascada de `partes_movimiento` → `objetivos` (viene de antes) quedaron en el plan del Sprint 4. Backend 75, frontend 28, base 27.
