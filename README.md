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

Fuera de tu PC el backend se corre con `ENTORNO=produccion`: así no usa ningún valor local y no arranca si falta alguna de esas tres variables o si el secreto es el de Supabase local.

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
- La API acepta hasta 120 pedidos por minuto por IP (`LIMITE_PEDIDOS_POR_MINUTO`); pasado eso responde 429. Detrás de un proxy (Render) arrancá uvicorn con `--proxy-headers --forwarded-allow-ips="*"`: si no, todos comparten la IP del proxy y el límite pasa a ser global.
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

- Tu plata es una sola: **disponible** (la plata del mes) + **ahorros**.
- Los **objetivos** son apartados dentro de ahorros; lo que no está apartado es **ahorro libre**.
- Mandar a ahorros, pasar a disponible, apartar o devolver son **transferencias**: no cuentan como gasto.
- Un **gasto se puede dividir** entre plata del mes, ahorro libre y objetivos. En el balance del mes es un solo gasto; cada bolsillo muestra solo su parte.
- Las **compras con tarjeta de crédito** no descuentan de tu plata: se acumulan en la tarjeta como deuda estimada, repartida en cuotas según el día de cierre. Lo que descuenta, y cuenta como gasto del mes, es el **pago del resumen** que cargás. Si pagás menos, el resto queda pendiente.
- Ningún saldo puede quedar en negativo.
