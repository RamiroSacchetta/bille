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
| T1 | S1, S2 | inline | en curso | — |
| T2 | S2 | inline | pendiente | — |
| T3 | S4 | inline | pendiente | — |
| T4 | S3 | inline | pendiente | — |
| T5 | S1–S4 | inline | pendiente | — |

- T1: URLs de API y Supabase según el host desde el que se abre la app; backend y frontend escuchando en la red local; CORS para IPs privadas.
- T2: íconos de Bille, build de producción servida localmente con service worker (instalable en la PC).
- T3: endpoint y botón para exportar movimientos a CSV.
- T4: cola offline en IndexedDB con reenvío automático al volver la conexión.
- T5: prueba de punta a punta.

## Log

- **L1** (2026-10-28) El usuario pidió "Sí, Sprint 2" y eligió la opción "A" ante el límite de HTTPS para instalar en el celular.
- **L2** (2026-10-28) La PC tiene IP de red local 192.168.0.10; Supabase local ya escucha en 0.0.0.0:54321.
