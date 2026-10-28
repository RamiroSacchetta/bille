# Sprint 2 — Calidad de la base

Bille instalable en la PC, usable desde el celular en la red local, carga offline en la PC y export a CSV.
Rama: `feat/sprint-2-calidad` (desde `feat/tarjetas-credito`) · Entrega: commits por unidad de trabajo · Tests: `pytest`, `ng test`.

## Specs

- **S1** — Opción elegida por el usuario: "A" = "PC instalable ahora, celular como web en tu Wi-Fi". El celular la usa desde el navegador sin instalar; la instalación en el celular queda para el Sprint 4 (HTTPS en la nube).
- **S2** — Del plan aprobado del Sprint 2: "PWA instalable en PC y celular dentro de la red local" (celular sin instalar, por S1).
- **S3** — Del plan aprobado: "cola offline para cargas manuales (IndexedDB)".
- **S4** — Del plan aprobado: "export CSV".
- **S5** — Del plan aprobado: "presupuestos mensuales por categoría (opcional)". Fuera de este sprint salvo que el usuario lo pida.

Supuestos: el CSV usa `;` como separador y coma decimal para que Excel en es-AR lo abra bien; la cola offline cubre gastos, ingresos y compras con tarjeta (no transferencias ni pagos de resumen); exponer la app en la red local requiere permitir los puertos en el firewall de Windows.

## Tasks

| ID | Specs | Ruta | Estado | Commit |
|----|-------|------|--------|--------|
| T1 | S1, S2 | inline | hecho | 5d74453 |
| T2 | S2 | inline | hecho | b31555e |
| T3 | S4 | inline | hecho | c2d3986 |
| T4 | S3 | inline | hecho | 1a2b85b |
| T5 | S1–S4 | inline | hecho (ver log) | — |

- T1: URLs de API y Supabase según el host desde el que se abre la app; backend y frontend escuchando en la red local; CORS para IPs privadas.
- T2: íconos de Bille, build de producción servida localmente con service worker (instalable en la PC).
- T3: endpoint y botón para exportar movimientos a CSV.
- T4: cola offline en IndexedDB con reenvío automático al volver la conexión.
- T5: prueba de punta a punta.

## Log

- **L1** (2026-10-28) El usuario pidió "Sí, Sprint 2" y eligió la opción "A" ante el límite de HTTPS para instalar en el celular.
- **L2** (2026-10-28) La PC tiene IP de red local 192.168.0.10; Supabase local ya escucha en 0.0.0.0:54321.
- **L3** (2026-10-28) Verificado: la app, la API y Supabase responden por 192.168.0.10 y CORS acepta ese origen (curl). El navegador integrado de la herramienta bloquea pedidos a 192.168.0.10:54321 (ERR_BLOCKED_BY_CLIENT, política del panel, no de Bille): la prueba real desde el celular queda para el usuario.
- **L4** (2026-10-28) Versión de producción en :8080 con service worker activo, contexto seguro y manifest "Bille" con 8 íconos (instalable en la PC). CSV probado con datos reales. Cola offline probada apagando el backend: "Café sin red" $ 5.000 quedó en "1 carga sin enviar" y se envió al volver (tu plata $ 680.000 → $ 675.000). Tests: backend 63, frontend 22.
- **L5** (2026-10-28) S5 (presupuestos por categoría) queda fuera del sprint, como estaba previsto ("opcional").
