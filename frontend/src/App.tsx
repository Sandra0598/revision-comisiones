import { useEffect, useState } from "react";
import axios from "axios";
import Layout, { Card } from "./components/Layout";
import FileUpload from "./components/FileUpload";
import ConfigForm from "./components/ConfigForm";
import ResultsSummary from "./components/ResultsSummary";
import PairContestCard from "./components/PairContestCard";
import IncidentsTable from "./components/IncidentsTable";
import DownloadBox from "./components/DownloadBox";
import RulesAccordion from "./components/RulesAccordion";
import { analyzeCommissions, getDefaultConfig } from "./api/commissionApi";
import type { AnalyzeResponse, Config } from "./types/commission";

const FALLBACK_CONFIG: Config = {
  importe_concurso_equipo_1: 0,
  importe_concurso_equipo_2: 0,
  equipo_1: ["Sara", "Eva", "Virginia", "Isamar"],
  equipo_2: ["Bea", "Laura", "Susana", "Estela"],
  importe_concurso_mensual: 0,
  premio_ventas_nuevas_499: 225,
  minimo_ventas_nuevas_499: 6,
  ventas_obligatorias_individual: 25,
  ventas_obligatorias_pareja: 50,
  objetivo_pizarra_1: 13,
  objetivo_pizarra_2: 12,
  referencia_frias_100: 13,
  referencia_upselling_100: 7,
  equivalencia_upselling_a_fria: 0.5,
  adw_bloque_para_punto: 3,
  rns_bloque_para_punto: 4,
  importes_venta_doble: [759, 859],
  importe_venta_doble: 859,
  activar_venta_doble_859: true,
  aplicar_premios_solo_si_100_concurso: true,
  modalidad_porcentaje_concurso: "pizarra_1_y_pizarra_2",
  pareja_fija: ["Eva", "Sara"],
  autorizacion_raul: "Pendiente",
  permitir_extrapolar_rappel_bonus: false,
};

function isValidExcel(file: File): boolean {
  const name = file.name.toLowerCase();
  return name.endsWith(".xlsx") || name.endsWith(".xls");
}

/** Validación de frontend antes de enviar. Devuelve mensaje de error o null. */
function validate(file: File | null, config: Config): string | null {
  if (!file) return "Debes seleccionar un archivo Excel antes de analizar.";
  if (!isValidExcel(file)) return "El archivo debe ser .xlsx o .xls.";
  if (
    (config.importe_concurso_equipo_1 ?? 0) < 0 ||
    (config.importe_concurso_equipo_2 ?? 0) < 0
  )
    return "Los importes del concurso por equipo deben ser mayores o iguales que 0.";
  const aut = config.autorizacion_raul ?? "Pendiente";
  if (!["Sí", "No", "Pendiente"].includes(aut))
    return "La autorización de Raúl debe ser Sí, No o Pendiente.";
  return null;
}

export default function App() {
  const [config, setConfig] = useState<Config>(FALLBACK_CONFIG);
  const [configLoaded, setConfigLoaded] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);

  // Cargar configuración por defecto del backend.
  useEffect(() => {
    let cancelled = false;
    getDefaultConfig()
      .then((cfg) => {
        if (!cancelled) {
          setConfig((prev) => ({ ...prev, ...cfg }));
          setConfigLoaded(true);
        }
      })
      .catch(() => {
        // Si falla, se usan los valores de respaldo.
        if (!cancelled) setConfigLoaded(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleAnalyze() {
    setError(null);
    const v = validate(file, config);
    setValidationError(v);
    if (v || !file) return;

    setLoading(true);
    setResult(null);
    try {
      const res = await analyzeCommissions(file, config);
      setResult(res);
      // Desplazar a resultados.
      setTimeout(() => {
        document
          .getElementById("resultados")
          ?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 50);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const detail =
          (err.response?.data as { detail?: string } | undefined)?.detail;
        setError(
          detail ??
            (err.code === "ERR_NETWORK"
              ? "No se pudo conectar con el backend. ¿Está en marcha en http://localhost:8000?"
              : `Error del servidor (${err.response?.status ?? "?"}).`)
        );
      } else {
        setError("Se produjo un error inesperado al analizar el archivo.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <Layout>
      {/* Subida de archivo */}
      <Card
        title="1. Sube el Excel de ventas"
        subtitle="Formatos admitidos: .xlsx y .xls"
      >
        <FileUpload
          file={file}
          onFileSelected={(f) => {
            setFile(f);
            setValidationError(null);
          }}
        />
      </Card>

      {/* Configuración */}
      <ConfigForm
        config={config}
        onChange={setConfig}
        loading={loading || !configLoaded}
      />

      {/* Botón principal */}
      <div className="flex flex-col gap-3">
        <button
          type="button"
          onClick={handleAnalyze}
          disabled={loading}
          className="inline-flex items-center justify-center gap-2 self-start rounded-lg bg-brand-600 px-6 py-3 text-base font-semibold text-white shadow-soft transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? (
            <>
              <svg
                className="h-5 w-5 animate-spin"
                viewBox="0 0 24 24"
                fill="none"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                />
              </svg>
              Analizando…
            </>
          ) : (
            "Analizar comisiones"
          )}
        </button>

        {validationError && (
          <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-medium text-amber-800">
            {validationError}
          </div>
        )}
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
            {error}
          </div>
        )}
      </div>

      {/* Resultados */}
      {result && (
        <div id="resultados" className="space-y-6">
          <DownloadBox filename={result.filename} />

          <ResultsSummary
            data={result.resumen_general}
            mes={result.mes_revision}
            anio={result.anio_revision}
          />

          {result.concurso_pareja_eva_sara && (
            <PairContestCard pareja={result.concurso_pareja_eva_sara} />
          )}

          <IncidentsTable incidencias={result.incidencias} />
        </div>
      )}

      {/* Reglas aplicadas (siempre visible) */}
      <RulesAccordion />
    </Layout>
  );
}
