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
