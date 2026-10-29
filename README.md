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
