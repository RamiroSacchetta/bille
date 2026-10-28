# Sprint 1 — MVP manual en local

Objetivo: los dos usuarios se registran, cargan ingresos, gastos (incluido pago dividido), ahorros y objetivos a mano, todo en local.
Rama: `feat/sprint-1-mvp` · Entrega: commits por unidad de trabajo en la rama (sin remoto todavía; la estrategia de PR se decide al tener remoto).
Tests: `pytest` (backend), `ng test` (frontend).

## Specs

- **S1** — Dos cuentas separadas. "Me gustaria que lo podamos usar yo y mi novia, con 2 cuentas separadas" · "separados por ahora 100%". Cada usuario ve solo sus datos.
- **S2** — Carga manual. "Gestión manual: Carga de gastos diarios en efectivo e ingresos."
- **S3** — Local primero. "primero que funcione en local".
- **S4** — Ahorros como bolsillo general con objetivos. "lo de fondo de emergencias no me gusta, deberia ser algo mas como ahorros, y de ahorros poder destinar algo para objetivos a largo plazo por ejemplo un viaje".
- **S5** — Gasto pagado con ahorros, con motivo. "si saco plata de mis ahorros para poder pagar el arreglo de un auto deberia poder decir che saque plata de mis ahorros para pagar esto".
- **S6** — Ese gasto cuenta en el balance del mes. "el arreglo de un auto, por ejemplo, un imprevisto, es un gasto que tiene que estar anotado en el balance del mes."
- **S7** — Pago dividido. "Puedo poner en anotación del gasto gasté 50 que tenía para gastar y $50 de los ahorros, pero que el total global sea 1, pero cuando vos entras en ahorros sea solamente el que vos destinaste para ahorros." · Orígenes posibles: plata del mes, ahorro libre "También objetivos".
- **S8** — Idioma. "en espanol hablame, codea y comenta tambien en espanol".
- **S9** — Diseño. Dirección "A" (Bosque) y mockups aprobados: https://claude.ai/artifact/HGN4efx3eZSGv9Y6TQ7wvd

Supuestos (no pedidos explícitamente): transferencias entre bolsillos no cuentan como gasto; ningún saldo puede quedar negativo; moneda única ARS en el MVP.

## Tasks

| ID | Specs | Ruta | Estado | Commit |
|----|-------|------|--------|--------|
| T1 | S3 | inline | hecho | 8daecb4 |
| T2 | S1, S4–S7 | inline | hecho (pgTAP 12/12) | 21a072b |
| T3 | S4–S7 | inline | hecho (21 tests) | f12bee7 |
| T4 | S1, S2 | inline | hecho (30 tests + 4 de integración contra Postgres) | e5cd582, f1171d6 |
| T5 | S1, S8, S9 | inline | hecho (build ok) | 4ff8d68 |
| T6 | S2, S4–S7, S9 | inline | hecho (8 tests de formato y división) | 4ff8d68 |
| T7 | S1–S7 | inline | hecho (prueba manual en el navegador con dos cuentas) | 582f2bb |

- T1: repo, `.gitignore`, README, Supabase CLI local (`supabase init`).
- T2: migración SQL (tablas, RLS, trigger de cuadre de partes, seed al crear perfil).
- T3: backend — dominio, casos de uso y tests unitarios (gasto dividido, transferencias, saldos no negativos).
- T4: backend — API REST, auth con JWT de Supabase, repositorios Postgres, tests de aislamiento.
- T5: frontend — scaffold Angular PWA, tokens de diseño, login, interceptor, guard.
- T6: frontend — Inicio, Movimientos, Carga rápida, Dividir el pago, Ahorros, Detalle de objetivo, Ajustes.
- T7: prueba local de punta a punta con dos cuentas.

Ruta: todas inline (sin razón de escritor delegado: unidades secuenciales y dependientes).

## Log

- **L1** (2026-10-28) Pedido original: PWA de finanzas personales con Angular + FastAPI + PostgreSQL; MVP con "Gestión manual", "Integración con Mercado Pago" y "Gestión de ahorros". Ajuste del usuario: "Me gustaria que lo podamos usar yo y mi novia, con 2 cuentas separadas, tambien me gustaria que me separes la implementacion en sprints desde ahora, emepezando con el mvp que va a ser todo manual, y despues que tengamos hecho la base, vamos ir haciendo features, de implementar mercado pago o otro tipo de api y despliegue en nube, primero que funcione en local".
- **L2** (2026-10-28) Modelo de ahorros acordado (S4–S7) y mockups aprobados: "Aprobar, Sprint 1".
- **L3** (2026-10-28) Decisión técnica: las migraciones viven en `supabase/migrations` (SQL) en lugar de Alembic, porque referencian `auth.users`, RLS y triggers.
- **L4** (2026-10-28) Decisión técnica: el backend usa psycopg 3 con SQL explícito (sin SQLAlchemy). Cada request toma `role authenticated` y fija `request.jwt.claims`, así RLS aplica también al backend. El commit se hace dentro del endpoint para que el error del cuadre diferido llegue al manejador HTTP.
- **L5** (2026-10-28) Bloqueo: Docker Desktop no arranca (el backend se cae al no poder borrar `AppData/Local/Docker/run/sailor-ingest.sock`). Sin Docker no se puede levantar Supabase local, correr `supabase test db` (pgTAP en `supabase/tests/database/esquema.test.sql`) ni la prueba de punta a punta. Tests del front: Karma necesita `CHROME_BIN` apuntando a Edge (`C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe`).
- **L7** (2026-10-28) El usuario reinició Docker. `supabase start` aplicó la migración; la clave anónima y el secreto JWT coinciden con los valores por defecto. pgTAP 12/12, backend 34 tests (30 unitarios + 4 de integración), frontend 8 tests. Prueba en el navegador (375×812): registro de Ana, sueldo $ 1.250.000, mandar $ 400.000 a ahorros, objetivo "Viaje a Bariloche", apartar $ 100.000, gasto "Arreglo del auto" $ 100.000 dividido 50.000 mes + 30.000 libre + 20.000 viaje → total $ 1.150.000, para gastar $ 800.000, ahorrado $ 350.000, libre $ 270.000, viaje $ 80.000, gastos del mes $ 100.000. Beto, recién registrado, ve todo en cero. Sin errores en consola.
- **L6** (2026-10-28) Próximo paso (resuelto en L7): con Docker andando, `npm run bd:iniciar`, `npx supabase test db`, verificar que `supabase status` coincida con la clave anónima y el secreto JWT de `frontend/src/environments/entorno.ts` y `backend/app/config.py`, levantar backend y frontend y probar con dos cuentas.
