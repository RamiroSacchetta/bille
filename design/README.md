# Bille — Diseño (Sprint 0)

Canvas: https://claude.ai/artifact/HGN4efx3eZSGv9Y6TQ7wvd (privado hasta compartirlo desde su menú Share)

Estado: **borrador — pendiente de aprobación**

## Pantallas (celular, 390×844)

| Lámina | Propósito |
|--------|-----------|
| Iniciar sesión | Ingreso y registro con email y contraseña |
| Inicio | Balance del mes, ingresos vs gastos, resumen de objetivos, últimos movimientos |
| Carga rápida | Selector gasto/ingreso, monto con teclado, chips de categoría y método de pago, guardar |
| Movimientos | Selector de mes, filtro Todos/Gastos/Ingresos, lista agrupada por día |
| Dividir el pago | Repartir un gasto entre plata del mes, ahorro libre y objetivos; las partes deben sumar el total |
| Ahorros | Total ahorrado con barra por destino (libre + objetivos), mandar/pasar plata, objetivos, últimos movimientos |
| Detalle de objetivo | Lo apartado, apartar desde ahorro libre o devolver, historial (incluye gastos pagados con el objetivo) |
| Ajustes | Perfil, categorías, métodos de pago (activar/desactivar), moneda, cerrar sesión |

Todas las láminas excepto Tokens se pueden recorrer en modo Play (barra inferior + links).

## Tokens

| Token | Valor | Uso |
|-------|-------|-----|
| tinta | `#111412` | Texto |
| atenuado | `#5B625E` | Texto secundario |
| fondo | `#F5F5F0` | Fondo de la app |
| linea | `#E3E4DE` | Bordes |
| superficie | `#FFFFFF` | Tarjetas |
| bosque | `#10231C` | Tarjetas destacadas, botones primarios |
| bosque-2 | `#1A3329` | Bloques dentro de tarjetas destacadas |
| lima | `#C8F169` | Acento sobre bosque |
| ingreso | `#0B63A8` | Montos positivos |
| gasto | `#B2470F` | Montos negativos |

- Tipografía: DM Sans (400/500/600/700) para la interfaz, DM Mono con números tabulares para todos los montos.
- Radios: 12 íconos · 18 tarjetas · 24 tarjetas destacadas · píldoras completas.
- Espaciado: 4 · 8 · 12 · 16 · 20 · 24 · 32; margen de pantalla 20 px; áreas táctiles ≥ 44 px.
- Los colores de ingreso y gasto difieren en luminosidad, no solo en tono (aptos para daltonismo).

## Idioma y formato

- Interfaz en español rioplatense (voseo), `lang="es"`.
- Montos con formato `es-AR`: `$ 1.234.567,89`; signo `−` para gastos.
- Código, identificadores, comentarios y documentación del proyecto en español.

## Revisión con la guía de diseño

- Áreas táctiles llevadas a 44 px (chips, filtros, selectores segmentados).
- "Cobrado en" para ingresos en Carga rápida, con métodos propios (Efectivo, Banco, Mercado Pago).
- Links "Ver todos" con nombre accesible distinto.
- Bordes de tarjeta solo en elementos interactivos; las listas van sin borde.

## Modelo de plata

- La plata es una sola: total = disponible (plata del mes) + ahorros.
- Ahorros es un bolsillo general; los objetivos son apartados dentro de ahorros. Ahorro libre = ahorros − apartados.
- Mandar a ahorros, pasar a disponible, apartar y devolver son transferencias: no cuentan como gasto.
- Un gasto puede pagarse dividido (plata del mes + ahorro libre + objetivos). En el balance es un solo gasto;
  cada bolsillo u objetivo muestra solo su parte.

## Dirección visual

- Elegida: **Opción A · Bosque** (la de las pantallas).
- Descartadas: Opción B · Celeste y Opción C · Ticket (quedan en el canvas como referencia).

## Pendientes

- Modo oscuro y versión de escritorio sin dibujar.
