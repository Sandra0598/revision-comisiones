// Tipos del dominio de revisión de comisiones.
//
// Nota: el backend devuelve algunos nombres distintos (p.ej. `nombre_archivo`,
// `puntos_adw`, `total_final`, `fila_original`, gravedad "baja|media|alta").
// El adaptador en `api/commissionApi.ts` normaliza la respuesta cruda del
// backend a estos tipos limpios que consume la interfaz.

export type AutorizacionRaul = "Sí" | "No" | "Pendiente";

export interface Config {
  importe_concurso_equipo_1: number;
  importe_concurso_equipo_2: number;
  equipo_1?: string[];
  equipo_2?: string[];
  importe_concurso_mensual: number;
  premio_ventas_nuevas_499: number;
  minimo_ventas_nuevas_499: number;
  ventas_obligatorias_individual: number;
  ventas_obligatorias_pareja: number;
  objetivo_pizarra_1: number;
  objetivo_pizarra_2: number;
  referencia_frias_100: number;
  referencia_upselling_100: number;
  equivalencia_upselling_a_fria: number;
  adw_bloque_para_punto: number;
  rns_bloque_para_punto: number;
  importes_venta_doble?: number[];
  importe_venta_doble: number;
  activar_venta_doble_859: boolean;
  aplicar_premios_solo_si_100_concurso: boolean;
  modalidad_porcentaje_concurso: string;
  comerciales_validas?: string[];
  pareja_fija?: string[];
  permitir_extrapolar_rappel_bonus?: boolean;

  // Datos auxiliares opcionales.
  meses_consecutivos_individual?: Record<string, number | string>;
  mes_consecutivo_pareja?: number | string;
  nivel_pareja_mes_anterior?: string;
  nivel_pareja_actual?: string;
  autorizacion_raul?: AutorizacionRaul;
  mes_revision?: number;
  anio_revision?: number;
}

export interface CommercialSummary {
  comercial: string;
  ventas_computables_totales: number;
  pizarra_1_final: number;
  pizarra_2_real: number;
  adw_computables: number;
  puntos_adw_pizarra_2: number;
  rns_computables: number;
  puntos_rns_pizarra_2: number;
  pizarra_2_ajustada: number;
  porcentaje_concurso: number;
  importe_concurso_obtenido: number;
  ventas_nuevas_499: number;
  premio_ventas_nuevas_499: number;
  ventas_para_rappel_bonus: number;
  rappel_bonus_general: number;
  ventas_para_rappel_individual: number;
  nivel_rappel_individual: string;
  mes_consecutivo_individual: string | number;
  rappel_individual: number;
  super_concurso_pareja: number;
  total_esperado: number;
  comision_declarada?: number;
  diferencia?: number;
  estado: string;
  alertas: string[];
}

export interface PairContestSummary {
  ventas_computables_eva: number;
  ventas_computables_sara: number;
  ventas_brutas_pareja: number;
  ventas_obligatorias_restadas: number;
  ventas_validas_pareja: number;
  porcentaje_concurso_eva: number;
  porcentaje_concurso_sara: number;
  aplica_pareja: boolean;
  nivel_pareja_actual: string;
  mes_consecutivo_pareja: string | number;
  premio_por_persona: number;
  autorizacion_raul: string;
  alerta?: string;
  importe_final_eva: number;
  importe_final_sara: number;
}

export type Gravedad = "info" | "warning" | "critical";

export interface Incident {
  fila?: number;
  comercial?: string;
  gravedad: Gravedad;
  tipo: string;
  descripcion: string;
}

export interface AnalyzeResponse {
  filename: string;
  resumen_general: CommercialSummary[];
  concurso_pareja_eva_sara?: PairContestSummary;
  incidencias: Incident[];
  mes_revision?: number;
  anio_revision?: number;
}
