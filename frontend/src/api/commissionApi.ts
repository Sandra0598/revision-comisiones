import { apiClient, API_BASE_URL } from "./client";
import type {
  AnalyzeResponse,
  CommercialSummary,
  Config,
  Gravedad,
  Incident,
  PairContestSummary,
} from "../types/commission";

// ---------------------------------------------------------------------------
// Tipos crudos que devuelve el backend (nombres reales de la API).
// ---------------------------------------------------------------------------

interface RawComercial {
  comercial: string;
  ventas_computables_totales: number;
  pizarra_1_final: number;
  pizarra_2_real: number;
  adw_computables: number;
  puntos_adw: number;
  rns_computables: number;
  puntos_rns: number;
  pizarra_2_ajustada: number;
  porcentaje_concurso: number;
  importe_concurso_obtenido: number;
  ventas_nuevas_499: number;
  premio_ventas_nuevas_499: number;
  ventas_para_rappel_bonus: number;
  rappel_bonus_general: number;
  ventas_para_rappel_individual: number;
  nivel_rappel_individual: string | null;
  mes_consecutivo_individual: string | number | null;
  rappel_individual: number;
  super_concurso_pareja: number;
  total_final: number;
  comision_declarada: number | null;
  diferencia: number | null;
  estado: string;
  alertas: string[];
}

interface RawPareja {
  ventas_computables_eva: number;
  ventas_computables_sara: number;
  ventas_brutas_pareja: number;
  ventas_obligatorias_restadas: number;
  ventas_validas_pareja: number;
  porcentaje_concurso_eva: number;
  porcentaje_concurso_sara: number;
  aplica_pareja: boolean;
  nivel_pareja_actual: string | null;
  mes_consecutivo_pareja: string | number | null;
  premio_por_persona: number;
  autorizacion_raul: string;
  alerta: string | null;
  importe_final_eva: number;
  importe_final_sara: number;
}

interface RawIncidencia {
  fila_original: number | null;
  comercial: string | null;
  tipo: string;
  descripcion: string;
  gravedad: string; // "baja" | "media" | "alta"
}

interface RawAnalyzeResponse {
  mes_revision: number;
  anio_revision: number;
  nombre_archivo: string;
  config_usada: Record<string, unknown>;
  resumen: RawComercial[];
  pareja: RawPareja | null;
  incidencias: RawIncidencia[];
  total_comerciales: number;
  total_ventas_procesadas: number;
}

// ---------------------------------------------------------------------------
// Adaptadores: backend -> tipos limpios de la interfaz.
// ---------------------------------------------------------------------------

function mapGravedad(g: string): Gravedad {
  switch (g) {
    case "alta":
      return "critical";
    case "media":
      return "warning";
    default:
      return "info";
  }
}

function mapComercial(r: RawComercial): CommercialSummary {
  return {
    comercial: r.comercial,
    ventas_computables_totales: r.ventas_computables_totales,
    pizarra_1_final: r.pizarra_1_final,
    pizarra_2_real: r.pizarra_2_real,
    adw_computables: r.adw_computables,
    puntos_adw_pizarra_2: r.puntos_adw,
    rns_computables: r.rns_computables,
    puntos_rns_pizarra_2: r.puntos_rns,
    pizarra_2_ajustada: r.pizarra_2_ajustada,
    porcentaje_concurso: r.porcentaje_concurso,
    importe_concurso_obtenido: r.importe_concurso_obtenido,
    ventas_nuevas_499: r.ventas_nuevas_499,
    premio_ventas_nuevas_499: r.premio_ventas_nuevas_499,
    ventas_para_rappel_bonus: r.ventas_para_rappel_bonus,
    rappel_bonus_general: r.rappel_bonus_general,
    ventas_para_rappel_individual: r.ventas_para_rappel_individual,
    nivel_rappel_individual: r.nivel_rappel_individual ?? "—",
    mes_consecutivo_individual: r.mes_consecutivo_individual ?? "—",
    rappel_individual: r.rappel_individual,
    super_concurso_pareja: r.super_concurso_pareja,
    total_esperado: r.total_final,
    comision_declarada: r.comision_declarada ?? undefined,
    diferencia: r.diferencia ?? undefined,
    estado: r.estado,
    alertas: r.alertas ?? [],
  };
}

function mapPareja(r: RawPareja): PairContestSummary {
  return {
    ventas_computables_eva: r.ventas_computables_eva,
    ventas_computables_sara: r.ventas_computables_sara,
    ventas_brutas_pareja: r.ventas_brutas_pareja,
    ventas_obligatorias_restadas: r.ventas_obligatorias_restadas,
    ventas_validas_pareja: r.ventas_validas_pareja,
    porcentaje_concurso_eva: r.porcentaje_concurso_eva,
    porcentaje_concurso_sara: r.porcentaje_concurso_sara,
    aplica_pareja: r.aplica_pareja,
    nivel_pareja_actual: r.nivel_pareja_actual ?? "—",
    mes_consecutivo_pareja: r.mes_consecutivo_pareja ?? "—",
    premio_por_persona: r.premio_por_persona,
    autorizacion_raul: r.autorizacion_raul,
    alerta: r.alerta ?? undefined,
    importe_final_eva: r.importe_final_eva,
    importe_final_sara: r.importe_final_sara,
  };
}

function mapIncidencia(r: RawIncidencia): Incident {
  return {
    fila: r.fila_original ?? undefined,
    comercial: r.comercial ?? undefined,
    gravedad: mapGravedad(r.gravedad),
    tipo: r.tipo,
    descripcion: r.descripcion,
  };
}

function normalizeResponse(raw: RawAnalyzeResponse): AnalyzeResponse {
  return {
    filename: raw.nombre_archivo,
    resumen_general: (raw.resumen ?? []).map(mapComercial),
    concurso_pareja_eva_sara: raw.pareja ? mapPareja(raw.pareja) : undefined,
    incidencias: (raw.incidencias ?? []).map(mapIncidencia),
    mes_revision: raw.mes_revision,
    anio_revision: raw.anio_revision,
  };
}

// ---------------------------------------------------------------------------
// Funciones públicas de la API.
// ---------------------------------------------------------------------------

/** GET /api/config/defaults */
export async function getDefaultConfig(): Promise<Config> {
  const { data } = await apiClient.get<Config>("/api/config/defaults");
  return data;
}

/** POST /api/analyze (multipart/form-data) */
export async function analyzeCommissions(
  file: File,
  config: Partial<Config>
): Promise<AnalyzeResponse> {
  const form = new FormData();
  form.append("file", file);
  form.append("config", JSON.stringify(config));
  if (config.mes_revision != null) {
    form.append("mes", String(config.mes_revision));
  }
  if (config.anio_revision != null) {
    form.append("anio", String(config.anio_revision));
  }

  const { data } = await apiClient.post<RawAnalyzeResponse>(
    "/api/analyze",
    form,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return normalizeResponse(data);
}

/** Devuelve la URL directa de descarga del Excel generado. */
export function downloadUrl(filename: string): string {
  return `${API_BASE_URL}/api/download/${encodeURIComponent(filename)}`;
}

/** GET /api/download/{filename} — descarga el Excel como blob y fuerza el guardado. */
export async function downloadReport(filename: string): Promise<void> {
  const { data, headers } = await apiClient.get(
    `/api/download/${encodeURIComponent(filename)}`,
    { responseType: "blob" }
  );

  // Intentar extraer el nombre amigable de la cabecera Content-Disposition.
  let downloadName = filename.includes("__")
    ? filename.split("__").slice(1).join("__")
    : filename;
  const disposition = headers["content-disposition"] as string | undefined;
  if (disposition) {
    const match = /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(disposition);
    if (match?.[1]) downloadName = decodeURIComponent(match[1]);
  }

  const blob = new Blob([data], {
    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = downloadName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}
