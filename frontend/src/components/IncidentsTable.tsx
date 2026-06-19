import type { Gravedad, Incident } from "../types/commission";
import { Card } from "./Layout";

interface IncidentsTableProps {
  incidencias: Incident[];
}

const GRAVEDAD_LABEL: Record<Gravedad, string> = {
  info: "Info",
  warning: "Aviso",
  critical: "Crítica",
};

function GravedadBadge({ gravedad }: { gravedad: Gravedad }) {
  const styles: Record<Gravedad, string> = {
    info: "bg-slate-100 text-slate-600 ring-slate-200",
    warning: "bg-amber-100 text-amber-800 ring-amber-200",
    critical: "bg-red-100 text-red-800 ring-red-200",
  };
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ${styles[gravedad]}`}
    >
      {GRAVEDAD_LABEL[gravedad]}
    </span>
  );
}

export default function IncidentsTable({ incidencias }: IncidentsTableProps) {
  const criticas = incidencias.filter((i) => i.gravedad === "critical").length;

  return (
    <Card
      title="Incidencias"
      subtitle={
        incidencias.length === 0
          ? "Sin incidencias detectadas."
          : `${incidencias.length} incidencia(s)${
              criticas ? ` · ${criticas} crítica(s)` : ""
            }`
      }
    >
      {incidencias.length === 0 ? (
        <p className="text-sm text-slate-500">
          No se han detectado incidencias en el análisis.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200">
            <thead>
              <tr className="bg-slate-100">
                <th className="px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Comercial
                </th>
                <th className="px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Fila
                </th>
                <th className="px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Gravedad
                </th>
                <th className="px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Tipo
                </th>
                <th className="px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Descripción
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {incidencias.map((inc, idx) => (
                <tr
                  key={idx}
                  className={
                    inc.gravedad === "critical" ? "bg-red-50" : "hover:bg-slate-50"
                  }
                >
                  <td className="px-3 py-2.5 text-sm text-slate-700">
                    {inc.comercial ?? "—"}
                  </td>
                  <td className="px-3 py-2.5 text-sm text-slate-500">
                    {inc.fila ?? "—"}
                  </td>
                  <td className="px-3 py-2.5">
                    <GravedadBadge gravedad={inc.gravedad} />
                  </td>
                  <td className="px-3 py-2.5 text-sm font-medium text-slate-700">
                    {inc.tipo}
                  </td>
                  <td className="px-3 py-2.5 text-sm text-slate-600">
                    {inc.descripcion}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}
