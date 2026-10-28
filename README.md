# Bille

Finanzas personales para dos personas con cuentas separadas: ingresos, gastos, ahorros y objetivos. PWA instalable en PC y celular.

## Estructura

```
backend/    API FastAPI (arquitectura hexagonal)
frontend/   App Angular (PWA)
supabase/   Configuración local de Supabase, migraciones SQL y tests de base de datos
design/     Mockups y tokens de diseño (Sprint 0)
odd/tasks/  Seguimiento por sprint
```

## Requisitos

- Docker Desktop corriendo
- Node 20+ y npm
- Python 3.12+ y [uv](https://docs.astral.sh/uv/)

## Levantar en local

Desde la raíz del repo, una vez:

```bash
npm install
```

Cada vez que quieras usar la app, en tres terminales:

```bash
npm run bd:iniciar
```

```bash
uv run --directory backend uvicorn app.main:app --port 8000
```

```bash
npm --prefix frontend start
```

Abrí http://127.0.0.1:4200 (o http://localhost:4200) y creá una cuenta por persona. Supabase Studio queda en http://127.0.0.1:54323 y los emails de prueba en http://127.0.0.1:54324.

Los valores de conexión locales (`backend/app/config.py` y `frontend/src/environments/entorno.ts`) son los que muestra `npx supabase status`. Para cambiarlos en el backend, creá `backend/.env` con `URL_BASE_DATOS`, `SUPABASE_URL` o `SUPABASE_JWT_SECRET`.

## Tests

```bash
npx supabase test db
```

```bash
uv run --directory backend pytest
```

```bash
npm --prefix frontend test -- --watch=false --browsers=ChromeHeadless
```

Los tests de integración del backend se saltean si Supabase local no está corriendo. Si Karma no encuentra Chrome, apuntá `CHROME_BIN` a Edge (`C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe`).

## Cómo funciona la plata

- Tu plata es una sola: **disponible** (la plata del mes) + **ahorros**.
- Los **objetivos** son apartados dentro de ahorros; lo que no está apartado es **ahorro libre**.
- Mandar a ahorros, pasar a disponible, apartar o devolver son **transferencias**: no cuentan como gasto.
- Un **gasto se puede dividir** entre plata del mes, ahorro libre y objetivos. En el balance del mes es un solo gasto; cada bolsillo muestra solo su parte.
- Ningún saldo puede quedar en negativo.
