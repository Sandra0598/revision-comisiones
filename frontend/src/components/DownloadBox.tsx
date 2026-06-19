import { useState } from "react";
import { downloadReport } from "../api/commissionApi";

interface DownloadBoxProps {
  filename: string;
}

export default function DownloadBox({ filename }: DownloadBoxProps) {
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Nombre amigable (sin el token "<hex>__").
  const displayName = filename.includes("__")
    ? filename.split("__").slice(1).join("__")
    : filename;

  async function handleDownload() {
    setError(null);
    setDownloading(true);
    try {
      await downloadReport(filename);
    } catch {
      setError("No se pudo descargar el archivo. Inténtalo de nuevo.");
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div className="flex flex-col items-start gap-3 rounded-xl border border-green-200 bg-green-50 p-5 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h3 className="text-base font-semibold text-green-900">
          Informe generado
        </h3>
        <p className="text-sm text-green-700">{displayName}</p>
        {error && <p className="mt-1 text-sm font-medium text-red-600">{error}</p>}
      </div>
      <button
        type="button"
        onClick={handleDownload}
        disabled={downloading}
        className="inline-flex items-center gap-2 rounded-lg bg-green-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-green-700 disabled:opacity-60"
      >
        {downloading ? (
          "Descargando…"
        ) : (
          <>
            <svg
              className="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.8}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3"
              />
            </svg>
            Descargar Excel revisado
          </>
        )}
      </button>
    </div>
  );
}
