// Tipos que devuelve la API. Los montos llegan como texto para no perder precisión.

export type TipoMovimiento = 'ingreso' | 'gasto' | 'transferencia' | 'cambio';
/** `disponible` y `ahorros` están en la moneda principal; `dolares` es aparte y nunca se suma a ellos. */
export type Bolsillo = 'disponible' | 'ahorros' | 'dolares';
/** Moneda de un bolsillo: 'ARS' es la moneda principal (se muestra según `MonedaPrincipal`) y 'USD' son los dólares. */
export type Moneda = 'ARS' | 'USD';
/** Cómo se muestra la moneda principal. No convierte montos. */
export type MonedaPrincipal = 'ARS' | 'BRL' | 'JPY' | 'EUR';

export interface Ubicacion {
  bolsillo: Bolsillo;
  objetivo_id?: string | null;
}

export interface Parte extends Ubicacion {
  monto: string;
}

export interface Movimiento {
  id: string;
  tipo: TipoMovimiento;
  /** En un cambio son los dólares comprados o vendidos. */
  monto: string;
  moneda: Moneda;
  ocurrido_en: string;
  descripcion: string | null;
  categoria_id: string | null;
  metodo_pago_id: string | null;
  tarjeta_id?: string | null;
  partes: Parte[];
}

export interface Objetivo {
  id: string;
  nombre: string;
  moneda: Moneda;
  monto_meta: string;
  fecha_meta: string | null;
  archivado: boolean;
  apartado: string;
}

export interface Resumen {
  saldos: {
    /** Solo pesos: disponible + ahorros. */
    total: string;
    disponible: string;
    ahorros: string;
    ahorro_libre: string;
    dolares: string;
    dolares_libres: string;
  };
  ingresos_mes: string;
  gastos_mes: string;
  gastos_dolares_mes: string;
  objetivos: Objetivo[];
  deuda_tarjetas: string;
  proximo_resumen_tarjetas: string;
}

export interface Categoria {
  id: string;
  nombre: string;
  tipo: 'ingreso' | 'gasto';
  icono: string | null;
}

export interface MetodoPago {
  id: string;
  nombre: string;
  tipo: string;
  activo: boolean;
}

export interface Perfil {
  id: string;
  nombre_visible: string;
  moneda_predeterminada: MonedaPrincipal;
}

export interface NuevoMovimientoBase {
  monto: string;
  ocurrido_en: string;
  descripcion?: string | null;
}

export interface NuevoGasto extends NuevoMovimientoBase {
  categoria_id?: string | null;
  metodo_pago_id?: string | null;
  origenes?: Parte[] | null;
  /** Lo genera el dispositivo: si la carga llega dos veces al servidor, se guarda una sola. */
  id_carga?: string;
}

export interface NuevoIngreso extends NuevoMovimientoBase {
  categoria_id?: string | null;
  metodo_pago_id?: string | null;
  destino?: Ubicacion;
  /** Lo genera el dispositivo: si la carga llega dos veces al servidor, se guarda una sola. */
  id_carga?: string;
}

/** Compra o venta de dólares: salen pesos y entran dólares, o al revés. */
export interface NuevoCambio {
  operacion: 'compra' | 'venta';
  dolares: string;
  pesos: string;
  ocurrido_en: string;
  /** De dónde salen los pesos al comprar o adónde van al vender; por defecto `disponible`. */
  pesos_en?: { bolsillo: 'disponible' | 'ahorros' };
  /** Lo genera el dispositivo: si la carga llega dos veces al servidor, se guarda una sola. */
  id_carga?: string;
  descripcion?: string | null;
}

export interface NuevoObjetivo {
  nombre: string;
  monto_meta: string;
  fecha_meta?: string | null;
  moneda?: Moneda;
}

export interface NuevaTransferencia extends NuevoMovimientoBase {
  desde: Ubicacion;
  hacia: Ubicacion;
}

export interface Tarjeta {
  id: string;
  nombre: string;
  dia_cierre: number;
  dia_vencimiento: number;
  activa: boolean;
  deuda_estimada: string;
  resumen_cerrado: string;
  resumen_en_curso: string;
  mes_en_curso: string;
  proximos: { mes: string; monto: string }[];
}

export interface Cuota {
  numero: number;
  monto: string;
  mes_resumen: string;
}

export interface CompraTarjeta {
  id: string;
  tarjeta_id: string;
  descripcion: string | null;
  categoria_id: string | null;
  monto_total: string;
  cantidad_cuotas: number;
  comprado_en: string;
  cuotas: Cuota[];
}

export interface NuevaCompraTarjeta {
  monto: string;
  cuotas: number;
  comprado_en: string;
  categoria_id?: string | null;
  descripcion?: string | null;
  /** Lo genera el dispositivo: si la carga llega dos veces al servidor, se guarda una sola. */
  id_carga?: string;
}

export interface PagoResumen extends NuevoMovimientoBase {
  origenes?: Parte[] | null;
}
