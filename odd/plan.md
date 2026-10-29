# Bille — PWA de Finanzas Personales

## Contexto
Proyecto desde cero (`C:\Users\Gamer\Desktop\DEV\Bille`). App de finanzas para **2 usuarios con cuentas y datos
100% separados**. Se construye por sprints: mockups (Sprint 0), MVP **manual y en local**, y después features
(Mercado Pago u otras APIs, nube, objetivos compartidos). **Todo en español**: chat, código, identificadores,
comentarios y documentación (las palabras clave del lenguaje/framework quedan como son).

## Decisiones clave
- **Backend: FastAPI** hexagonal (Pydantic + SQLAlchemy 2 + Alembic).
- **Local primero con Supabase CLI** (`supabase start`, Docker): Postgres + Auth + Studio. Mismas migraciones en la nube después.
- **Auth: Supabase Auth**, 2 usuarios. El backend valida el JWT y filtra por `usuario_id`; RLS como defensa en profundidad.
- **Dirección visual: Opción A "Bosque"** (ver `design/README.md`).
- **Dinero:** `numeric(14,2)` + `moneda char(3)`.
- **Modelo de plata (decidido con el usuario):**
  - La plata es una sola: **total = disponible + ahorros**.
  - **Ahorros** es un bolsillo general; los **objetivos** (ej. viaje) son *apartados* dentro de ahorros.
    Ahorro libre = ahorros − suma de apartados.
  - Mandar a ahorros, pasar a disponible, apartar o devolver de un objetivo son **transferencias**: no son gastos.
  - Un **gasto puede pagarse dividido** entre plata del mes, ahorro libre y uno o más objetivos.
    En el balance aparece un solo gasto por el total; cada bolsillo/objetivo solo ve su parte.
  - Balance del mes = ingresos − gastos (las transferencias no cuentan).

---

## Sprint 0 — Mockups visuales (Claude Design) ✅ en revisión
Canvas: https://claude.ai/artifact/HGN4efx3eZSGv9Y6TQ7wvd — 8 pantallas de celular + tokens + 2 direcciones descartadas.
Cierra cuando el usuario aprueba.

## Sprint 1 — MVP manual en local
Objetivo: los dos se registran/loguean y cargan todo a mano, en local.
1. `git init`, monorepo, `supabase init` + `supabase start`, FastAPI `/salud`, Angular + `ng add @angular/pwa`.
2. Migración inicial (esquema abajo) + seed de categorías y métodos de pago al crear el perfil.
3. Auth: login Supabase en Angular → interceptor JWT → `usuario_actual` en FastAPI.
4. Movimientos: alta/edición/baja de ingresos, gastos y transferencias; pago dividido; lista con filtros.
5. Ahorros: bolsillo general, objetivos, apartar/devolver, historial.
6. Inicio: tu plata (disponible + ahorros), ingresos/gastos del mes, objetivos, últimos movimientos.
7. Tokens del Sprint 0 en `compartido/ui`.

### Esquema MVP (referencia SQL; se escribe como migración Alembic)
```sql
create type tipo_movimiento as enum ('ingreso', 'gasto', 'transferencia');
create type bolsillo        as enum ('disponible', 'ahorros');
create type origen_carga    as enum ('manual');  -- 'mercadopago' se agrega en su sprint

create table perfiles (                          -- 1:1 con auth.users
  id uuid primary key references auth.users(id) on delete cascade,
  nombre_visible text not null,
  moneda_predeterminada char(3) not null default 'ARS',
  creado_en timestamptz not null default now()
);

create table metodos_pago (
  id uuid primary key default gen_random_uuid(),
  usuario_id uuid not null references perfiles(id) on delete cascade,
  nombre text not null,
  tipo text not null check (tipo in ('efectivo', 'billetera', 'debito', 'credito', 'banco')),
  activo boolean not null default true,
  unique (usuario_id, nombre)
);

create table categorias (
  id uuid primary key default gen_random_uuid(),
  usuario_id uuid not null references perfiles(id) on delete cascade,
  nombre text not null,
  tipo tipo_movimiento not null check (tipo in ('ingreso', 'gasto')),
  icono text,
  unique (usuario_id, nombre, tipo)
);

create table objetivos (                         -- apartados dentro del bolsillo de ahorros
  id uuid primary key default gen_random_uuid(),
  usuario_id uuid not null references perfiles(id) on delete cascade,
  nombre text not null,
  monto_meta numeric(14,2) not null check (monto_meta > 0),
  moneda char(3) not null default 'ARS',
  fecha_meta date,
  archivado boolean not null default false,
  creado_en timestamptz not null default now()
);

create table movimientos (                       -- lo que ve el usuario: un renglón por hecho
  id uuid primary key default gen_random_uuid(),
  usuario_id uuid not null references perfiles(id) on delete cascade,
  tipo tipo_movimiento not null,
  monto numeric(14,2) not null check (monto > 0), -- total, siempre positivo
  moneda char(3) not null default 'ARS',
  ocurrido_en timestamptz not null,
  descripcion text,
  categoria_id uuid references categorias(id) on delete set null,
  metodo_pago_id uuid references metodos_pago(id) on delete set null,
  origen origen_carga not null default 'manual',
  id_externo text,
  creado_en timestamptz not null default now(),
  unique (usuario_id, origen, id_externo)
);
create index movimientos_usuario_fecha_idx on movimientos (usuario_id, ocurrido_en desc);

create table partes_movimiento (                 -- de qué bolsillo/objetivo sale o entra cada parte
  id uuid primary key default gen_random_uuid(),
  movimiento_id uuid not null references movimientos(id) on delete cascade,
  bolsillo bolsillo not null,
  objetivo_id uuid references objetivos(id) on delete restrict,
  monto numeric(14,2) not null check (monto <> 0), -- con signo: + entra, − sale
  check (objetivo_id is null or bolsillo = 'ahorros')
);
create index partes_movimiento_mov_idx on partes_movimiento (movimiento_id);
create index partes_movimiento_obj_idx on partes_movimiento (objetivo_id) where objetivo_id is not null;
-- RLS en todas las tablas: usuario_id = auth.uid() (partes_movimiento vía su movimiento)
```

**Reglas de las partes** (validadas en el caso de uso y con un trigger de restricción diferido):
| Tipo | Suma de las partes | Ejemplo |
|---|---|---|
| ingreso | `+monto` | Sueldo: disponible +1.250.000 |
| gasto | `−monto` | Arreglo del auto 100.000: disponible −50.000, ahorros −30.000, ahorros/Viaje −20.000 |
| transferencia | `0` | Mandar a ahorros: disponible −100.000, ahorros +100.000 · Apartar: ahorros −50.000, ahorros/Viaje +50.000 |

**Saldos (consultas, no columnas):** disponible = Σ partes `disponible`; ahorros = Σ partes `ahorros`;
apartado de un objetivo = Σ partes con ese `objetivo_id`; ahorro libre = ahorros − Σ apartados.
Ningún saldo puede quedar negativo (validado al guardar).

### Estructura Angular (`frontend/src/app`) — screaming + container/presentational
```
nucleo/          autenticacion.servicio.ts, autenticacion.interceptor.ts, autenticacion.guard.ts, api.config.ts
compartido/ui/   campo-monto, etiqueta-monto, chip-categoria, barra-progreso, estado-vacio
funcionalidades/
  autenticacion/ contenedores/ingreso.pagina.ts
  movimientos/   datos/ (api + store con signals), contenedores/ (lista, carga, pago-dividido), ui/ (fila, filtros)
  catalogo/      categorías y métodos de pago
  ahorros/       datos/, contenedores/ (ahorros, detalle-objetivo), ui/ (apartar-form)
  inicio/        contenedores/inicio.pagina.ts
app.routes.ts    loadChildren lazy por funcionalidad, todo detrás del guard
```

### Backend (`backend/app`) — hexagonal
```
dominio/         entidades (Movimiento, ParteMovimiento, Objetivo) + puertos (RepositorioMovimientos, RepositorioObjetivos)
aplicacion/      casos de uso (registrar_gasto, registrar_ingreso, transferir, apartar_para_objetivo, consultar_saldos)
infraestructura/ repositorios sqlalchemy, bd.py, jwt_supabase.py
api/             routers/ (movimientos, categorias, metodos_pago, objetivos, inicio), dependencias.py
```

**Cierre del sprint:** los dos usuarios en local, cada uno carga movimientos (incluido un gasto dividido) y objetivos,
los saldos cuadran y **ninguno ve los datos del otro**.

---

## Tarjetas de crédito (agregado entre el Sprint 1 y el 2) ✅
Compras con tarjeta en cuotas como deuda estimada; solo el pago real del resumen descuenta y cuenta como gasto.
Seguimiento en `odd/tasks/tarjetas-credito.md`.

## Sprint 2 — Calidad de la base ✅
PC instalable, celular como web en la red local (opción A), cola offline para cargas manuales (IndexedDB), export CSV.
Presupuestos mensuales por categoría quedaron afuera (opcional). Seguimiento en `odd/tasks/sprint-2.md`.

## Sprint 3 — Seguridad y acceso (antes del deploy)
Mercado Pago salió de este lugar ("Quiero sacar el sprint 3, por que por ahora no voy a intregrar mercado pago o
otra api") y pasó al Sprint 6. En su lugar, lo necesario para salir a internet con amigos usando la app
("Podriamos agregar un sprint antes del deploy con estas cosas verdad ?"). Todo se configura y prueba en local
(Supabase CLI soporta Google, políticas de contraseña y registro desde `supabase/config.toml`) y se replica en la nube.
- **Entrar con Google** (OAuth de Supabase) además de email y contraseña. El cliente OAuth en Google Cloud lo crea el usuario.
- **Registro solo por invitación**: lista de emails permitidos, aplicada también a Google.
- **Contraseñas**: mínimo 8 caracteres y bloqueo de contraseñas filtradas.
- **Configuración segura**: el backend no arranca fuera de desarrollo si faltan variables de entorno (nada de secretos por defecto).
- **Límite de pedidos por minuto** en la API (fuerza bruta y abuso).
- **Encabezados de seguridad** (CSP, HSTS, etc.) preparados para Vercel.
- **Dependencias**: avisos automáticos de vulnerabilidades (Dependabot) al subir a GitHub.
- **Backups propios**: script de copia periódica de la base.

## Sprint 4 — Deploy en la nube
Plan gratis (decisión del usuario): Supabase cloud (mismas migraciones), backend en **Render free**, frontend en Vercel.
Con HTTPS, Bille se puede instalar y usar offline también en el celular.
- **Guardar primero, enviar después** (pedido del usuario, por la API dormida de Render): toda carga se guarda en el
  dispositivo antes de enviarse y solo se borra cuando el servidor confirma; si se cierra la app esperando, se envía
  al volver a abrirla.
- **Identificador único por carga** (idempotencia): el dispositivo genera un id; si el servidor lo recibe dos veces,
  devuelve lo ya guardado en lugar de duplicar. Aplica a gastos, ingresos y compras con tarjeta.
- Ajustes de deploy: URLs por entorno (local vs nube) en el frontend; psycopg con `prepare_threshold=None` para el
  pooler de Supabase; verificar login con las claves de firma nuevas (JWKS, ya soportado); CORS solo para el dominio
  real; secretos en variables de entorno.
- **Opción C (decisión del usuario):** la app LEE directo de Supabase (RLS + vistas de saldos, objetivos, deudas de
  tarjetas y totales del mes), así abre con los números al instante aunque Render esté dormido; ESCRIBE por la API en
  segundo plano con la cola. Tests que comparen los saldos de las vistas con los del backend.
- Al abrir la app se despierta la API (pedido a `/api/salud`) y nunca se muestra el estado vacío mientras se carga.
- Cuentas en GitHub, Supabase, Vercel y Render las crea el usuario; el repo se sube a GitHub.
- Registro solo por invitación: hecho en el Sprint 3.
- Pendientes que dejó el Sprint 3: en `frontend/vercel.json`, poner en `connect-src` las URLs reales de la API y de Supabase (hoy supone `*.onrender.com` y `*.supabase.co`), y que el frontend use HTTPS para la API (`upgrade-insecure-requests`); uvicorn con `--proxy-headers`; "Confirm email" activado en la nube; activar Google en la nube con su cliente OAuth y la URL de retorno de producción.
- Detectado en el Sprint 3, viene de antes: borrar un usuario que tiene movimientos asignados a objetivos falla, porque la FK compuesta `partes_movimiento` → `objetivos` no tiene `on delete cascade`. Hay que corregirlo antes de que alguien quiera borrar su cuenta.
- `scripts/backup.ps1` recibe la URL de la base como argumento de `supabase db dump`, así que se ve en la lista de procesos de la PC donde corre.

## Sprint 5 — Objetivos compartidos
Tabla `miembros_objetivo (objetivo_id, usuario_id, rol)`, invitación entre las dos cuentas, RLS ampliada; cada uno
aparta desde su cuenta y el progreso suma las partes de ambos.

## Sprint 6 — Integración Mercado Pago (u otra API) · más adelante, sin fecha
- Spike con el token real: `/users/me` + `/v1/payments/search`. **Riesgo:** la API pública devuelve de forma
  confiable los pagos *recibidos*; los salientes no están garantizados. El spike define el alcance.
- Tabla `conexiones_mp` (token cifrado con Fernet, nunca llega al frontend), `alter type origen_carga add value 'mercadopago'`.
- Endpoints de conexión, vista previa y sincronización idempotente por `id_externo`, detrás de un puerto `ProveedorPagos`.

---

## Forma de trabajo
- Un documento `odd/tasks/sprint-N.md` por sprint, branch por sprint, commits convencionales en español por unidad de trabajo.
- Cargar el skill `supabase-postgres-best-practices` antes de escribir la migración (Sprint 1).

## Verificación
- Sprint 0: diseño publicado y aprobado por el usuario.
- Sprint 1: `pytest` de casos de uso (gasto dividido suma −monto, transferencia suma 0, saldo negativo rechazado,
  aislamiento entre usuarios: B recibe 404/vacío sobre datos de A), test de RLS en Supabase local, `ng test` de stores,
  prueba manual con 2 cuentas en `localhost`.
- Sprint 4: smoke test sobre las URLs de nube + Lighthouse PWA instalable (PC y celular).
- Sprint 6: `respx` mockeando MP (approved/pending, 401 → 401, 5xx → 502, re-sync sin duplicados).
