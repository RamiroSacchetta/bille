// Tipos que devuelve la API. Los montos llegan como texto para no perder precisión.

export type TipoMovimiento = 'ingreso' | 'gasto' | 'transferencia';
export type Bolsillo = 'disponible' | 'ahorros';

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
  monto: string;
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
  monto_meta: string;
  fecha_meta: string | null;
  archivado: boolean;
  apartado: string;
}

export interface Resumen {
  saldos: { total: string; disponible: string; ahorros: string; ahorro_libre: string };
  ingresos_mes: string;
  gastos_mes: string;
  objetivos: Objetivo[];
  deuda_tarjetas: string;
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
  moneda_predeterminada: string;
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
}

export interface NuevoIngreso extends NuevoMovimientoBase {
  categoria_id?: string | null;
  metodo_pago_id?: string | null;
  destino?: Ubicacion;
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
}

export interface PagoResumen extends NuevoMovimientoBase {
  origenes?: Parte[] | null;
}
