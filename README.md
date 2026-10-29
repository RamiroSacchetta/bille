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
uv run --directory backend uvicorn app.main:app --host 0.0.0.0 --port 8000
```

```bash
npm --prefix frontend run produccion
```

Abrí http://127.0.0.1:8080 y creá una cuenta por persona. Supabase Studio queda en http://127.0.0.1:54323 y los emails de prueba en http://127.0.0.1:54324.

### Invitar a alguien

Bille es solo por invitación: solo se puede crear una cuenta (con email o con Google) si el email está en la tabla `invitaciones`. Para invitar a alguien, en Studio → SQL Editor:

```sql
insert into public.invitaciones (email) values ('amiga@ejemplo.com');
```

Las cuentas que ya existían siguen entrando normalmente. Las contraseñas nuevas llevan al menos 8 caracteres, con letras y números.

### Entrar con Google

El botón "Continuar con Google" aparece solo cuando el proveedor está activo. Para activarlo en local:

1. En [Google Cloud Console](https://console.cloud.google.com/apis/credentials) creá un **ID de cliente de OAuth** de tipo **Aplicación web**.
2. En "URI de redireccionamiento autorizados" agregá `http://127.0.0.1:54321/auth/v1/callback`.
3. Creá `supabase/.env` (no se sube a git) con:
   ```
   SUPABASE_AUTH_EXTERNAL_GOOGLE_CLIENT_ID=tu-id-de-cliente
   SUPABASE_AUTH_EXTERNAL_GOOGLE_SECRET=tu-secreto
   ```
4. En `supabase/config.toml`, en `[auth.external.google]`, poné `enabled = true` y reiniciá con `npx supabase stop` y `npx supabase start`.

La invitación también vale para Google: si el email de la cuenta de Google no está invitado, no entra. En la red local, Google solo funciona desde la PC (no acepta IPs privadas como retorno).

Para desarrollar con recarga automática, en lugar de `produccion` usá `npm --prefix frontend start` y abrí http://127.0.0.1:4200 (sin service worker, así que no se instala ni funciona offline).

### Instalar en la PC

Con la versión de producción abierta en http://127.0.0.1:8080, en Chrome, Edge o Brave usá el ícono de instalar de la barra de direcciones (o el menú → "Instalar Bille"). Queda como una app con su propia ventana. Funciona sin conexión: lo que cargues se guarda en la PC y se envía solo cuando vuelve la red.

### Usar desde el celular (misma red Wi-Fi)

1. Averiguá la IP de la PC con `ipconfig` (por ejemplo `192.168.0.10`).
2. En el celular abrí `http://192.168.0.10:8080`.
3. La primera vez, Windows puede pedir permiso para que Node, Python y Docker reciban conexiones: aceptá solo para **redes privadas**. Tienen que poder entrar los puertos 8080 (app), 8000 (API) y 54321 (Supabase).

En el celular Bille se usa desde el navegador: instalarla y usarla sin conexión requiere HTTPS, que llega con el despliegue en la nube (Sprint 4). Mientras tanto, cualquiera en tu Wi-Fi puede ver la pantalla de ingreso; los datos siguen protegidos por la cuenta de cada uno.

### Exportar a Excel

En Movimientos, "Exportar CSV" descarga los movimientos del mes elegido, listos para abrir en Excel (separador punto y coma, coma decimal).

Los valores de conexión locales (`backend/app/config.py` y `frontend/src/environments/entorno.ts`) son los que muestra `npx supabase status`. Para cambiarlos en el backend, creá `backend/.env` con `URL_BASE_DATOS`, `SUPABASE_URL` o `SUPABASE_JWT_SECRET`.

Fuera de tu PC el backend se corre con `ENTORNO=produccion`: así no usa ningún valor local, y no arranca si falta alguna de esas tres variables o `ORIGENES_CORS` (el dominio de la app), ni si el secreto es el de Supabase local. En producción solo acepta pedidos de los dominios de `ORIGENES_CORS`.

## Deploy en la nube

Gratis: base y login en **Supabase**, API en **Render**, app en **Vercel**. Las cuentas las creás vos; ningún secreto va al repo. Hacelo en este orden:

### 1. Supabase

1. Creá un proyecto en la misma región que la API de Render (Oregon, `us-west-2`) y guardá la contraseña de la base. La API hace varias consultas por pantalla: conviene que esté al lado de la base, y Render gratis no tiene servidores en Sudamérica.
2. Subí las migraciones desde la raíz del repo:
   ```bash
   npx supabase login
   ```
   ```bash
   npx supabase link --project-ref TU-REF
   ```
   ```bash
   npx supabase db push
   ```
3. En **Authentication**:
   - **Hooks**: activá **Before User Created** con la función de Postgres `public.hook_antes_de_crear_usuario` (es la que exige invitación).
   - **Providers → Email**: dejá **Confirm email** activado y poné la contraseña mínima en 8 con letras y números.
   - **URL Configuration**: en Site URL y Redirect URLs va la dirección de Vercel (la tenés en el paso 4; volvé acá después), con `/**` al final en Redirect URLs.
4. Copiá estos datos:
   - De **Connect → Session pooler**: la cadena de conexión. Render no tiene IPv6, así que la conexión directa no funciona.
   - **Project URL** y **anon / publishable key**.
   - El **JWT secret** (en JWT Keys, el "Legacy JWT secret").

### 2. La app apunta a tu Supabase

En [`frontend/src/environments/entorno.ts`](frontend/src/environments/entorno.ts), completá `NUBE` con la Project URL y la clave anónima. Esos dos valores son públicos por diseño. Commiteá y subí el cambio.

### 3. Render (API)

1. **New → Blueprint** y elegí el repo. Render lee [`render.yaml`](render.yaml).
2. Completá las variables:
   - `URL_BASE_DATOS`: la cadena del Session pooler.
   - `SUPABASE_URL`: la Project URL.
   - `SUPABASE_JWT_SECRET`: el JWT secret.
   - `ORIGENES_CORS`: la dirección de Vercel como lista, por ejemplo `["https://bille.vercel.app"]`. Si todavía no la tenés, poné algo provisorio y cambialo después del paso 4.
3. Si Render te da otra dirección que `https://bille-api.onrender.com`, corregí `apiUrl` en `NUBE`.

### 4. Vercel (app)

**Add New → Project**, elegí el repo y poné **Root Directory** en `frontend`. El resto lo toma de [`frontend/vercel.json`](frontend/vercel.json). Con la dirección que te da, completá `ORIGENES_CORS` en Render y las URLs de Supabase (paso 1.3).

### 5. Que la API no se duerma

Render gratis se duerme a los 15 minutos sin uso y tarda cerca de un minuto en despertar. En [cron-job.org](https://cron-job.org) (o UptimeRobot), creá un pedido `GET` a `https://bille-api.onrender.com/api/salud` cada 10 minutos.

Un servicio prendido todo el mes usa unas 744 de las 750 horas gratis de Render. Si dejás de usar la app, borrá el cron.

### 6. Invitar y probar

1. En Supabase → **SQL Editor**, invitá a cada persona: `insert into public.invitaciones (email) values ('amiga@ejemplo.com');`.
2. Abrí la dirección de Vercel en el celular, creá la cuenta (llega un email para confirmarla) y en el menú del navegador elegí **Instalar app** o **Agregar a la pantalla de inicio**.

Para activar **Google** en la nube, seguí los mismos pasos de "Entrar con Google", con estas diferencias:
- El URI de redireccionamiento es `https://TU-REF.supabase.co/auth/v1/callback`.
- El proveedor se activa en **Authentication → Providers → Google**.

### Cómo se porta con la red

Toda carga se guarda primero en el dispositivo, con un id único, y recién después se envía. Si la API tarda o no hay red, queda guardada y se manda sola al abrir la app o al volver la conexión. Si una carga llega dos veces, la API devuelve la ya guardada en lugar de duplicarla.

Al abrir, la app despierta la API. Si tarda más de 5 segundos, se muestran los últimos números que vio.

## Copias de seguridad

`scripts/backup.ps1` guarda roles, esquema y datos (incluidas las cuentas) en `backups/AAAA-MM-DD_HHmm` y conserva las últimas 14 copias. Necesita Docker corriendo. Sin configuración copia el Supabase local; para la nube, definí antes la cadena de conexión de Supabase (Settings → Database):

```powershell
$env:BILLE_URL_BASE_DATOS_BACKUP = "postgresql://postgres.xxxx:clave@aws-0-sa-east-1.pooler.supabase.com:5432/postgres"
.\scripts\backup.ps1
```

Para que corra solo todos los días a las 3, con el Programador de tareas de Windows (la variable tiene que estar definida a nivel usuario):

```powershell
schtasks /Create /SC DAILY /ST 03:00 /TN "Bille backup" /TR "powershell -NoProfile -File C:\ruta\a\Bille\scripts\backup.ps1"
```

`backups/` no se sube a git: guardá una copia en otro lado (un disco externo o tu nube personal). Para restaurar, seguí la [guía de Supabase](https://supabase.com/docs/guides/platform/migrating-within-supabase/backup-restore) con `roles.sql`, `esquema.sql` y `datos.sql` en ese orden.

## Seguridad

- Registro solo por invitación y contraseñas de al menos 8 caracteres con letras y números (ver "Invitar a alguien").
- La API acepta hasta 120 pedidos por minuto por IP (`LIMITE_PEDIDOS_POR_MINUTO`); pasado eso responde 429. Detrás de un proxy (Render) uvicorn arranca con `--proxy-headers --forwarded-allow-ips="*"` (ya está en `render.yaml`): si no, todos comparten la IP del proxy y el límite pasa a ser global.
- En Supabase de la nube dejá activado **Confirm email** (Authentication → Providers → Email). Sin eso, alguien que conozca el email de un invitado podría registrarlo primero con una contraseña propia.
- `frontend/vercel.json` define los encabezados de seguridad (CSP, HSTS, etc.) para el despliegue en Vercel.
- `.github/dependabot.yml` activa avisos y actualizaciones de dependencias cuando el repo esté en GitHub.

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

- Tu plata es una sola: **disponible** (la plata del mes) + **ahorros**. En el inicio lo grande es lo disponible; el total y lo ahorrado van debajo.
- Los **objetivos** son apartados dentro de ahorros; lo que no está apartado es **ahorro libre**.
- Agregar a ahorros, pasar a disponible, apartar o devolver son **movimientos internos**: no cuentan como gasto.
- Un **gasto se puede dividir** entre plata del mes, ahorro libre y objetivos. En el balance del mes es un solo gasto; cada bolsillo muestra solo su parte.
- Las **compras con tarjeta de crédito** no descuentan de tu plata: se acumulan en la tarjeta como deuda estimada, repartida en cuotas según el día de cierre. Lo que descuenta, y cuenta como gasto del mes, es el **pago del resumen** que cargás. Si pagás menos, el resto queda pendiente. En el inicio se ve el **próximo resumen**, lo que se suele pagar con el sueldo que viene: el último resumen cerrado (con lo atrasado) mientras no esté pago, y después el que está en curso.
- Los **dólares** son un bolsillo aparte que nunca se convierte: no suman al total en pesos ni a los ingresos o gastos del mes.
  - **Comprar o vender dólares** es un **cambio**: salen pesos (de la plata del mes o del ahorro libre) y entran dólares, o al revés. Se guardan los dos montos, así queda a cuánto cambiaste.
  - **"Ya los tenía"** es un ingreso en dólares.
  - Los **gastos en dólares** salen de los dólares libres o de un objetivo en dólares, y el inicio los muestra aparte ("Gastos en dólares").
  - Un **objetivo** es en pesos o en dólares: el de pesos se aparta desde ahorros y el de dólares, desde los dólares.
  - Un gasto o un movimiento interno van en una sola moneda; para pasar de una a otra se compra o se vende. El pago de una tarjeta es siempre en pesos.
- Ningún saldo puede quedar en negativo, en ninguna de las dos monedas.
