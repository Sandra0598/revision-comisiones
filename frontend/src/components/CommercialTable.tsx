import type { CommercialSummary } from "../types/commission";
import { formatCurrency, formatNumber, formatPercent } from "../utils/formatters";

interface CommercialTableProps {
  data: CommercialSummary[];
}

/** Normaliza el estado del backend (sin tildes) a una clave estable. */
function estadoKey(estado: string): "correcta" | "mas" | "menos" | "nc" {
  const e = estado.toLowerCase();
  if (e.includes("correcta")) return "correcta";
  if (e.includes("menos")) return "menos";
  if (e.includes("mas") || e.includes("más")) return "mas";
  return "nc";
}

function EstadoBadge({ estado }: { estado: string }) {
  const key = estadoKey(estado);
  const styles: Record<string, string> = {
    correcta: "bg-green-100 text-green-800 ring-green-200",
    mas: "bg-amber-100 text-amber-800 ring-amber-200",
    menos: "bg-red-100 text-red-800 ring-red-200",
    nc: "bg-slate-100 text-slate-600 ring-slate-200",
  };
  return (
    <span
      className={`inline-flex whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ${styles[key]}`}
    >
      {estado}
    </span>
  );
}

function diffClass(diff?: number): string {
  if (diff === undefined) return "text-slate-400";
  if (Math.abs(diff) < 0.01) return "text-green-700";
  return diff > 0 ? "text-amber-700" : "text-red-700";
}

const TH = ({ children, right }: { children: React.ReactNode; right?: boolean }) => (
  <th
    className={`sticky top-0 z-10 whitespace-nowrap bg-slate-100 px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-slate-500 ${
      right ? "text-right" : "text-left"
    }`}
  >
    {children}
  </th>
);

const TD = ({
  children,
  right,
  className = "",
}: {
  children: React.ReactNode;
  right?: boolean;
  className?: string;
}) => (
  <td
    className={`whitespace-nowrap px-3 py-2.5 text-sm text-slate-700 ${
      right ? "text-right tabular-nums" : ""
    } ${className}`}
  >
    {children}
  </td>
);

export default function CommercialTable({ data }: CommercialTableProps) {
  if (data.length === 0) {
    return <p className="text-sm text-slate-500">No hay comerciales que mostrar.</p>;
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200">
      <table className="min-w-full divide-y divide-slate-200">
        <thead>
          <tr>
            <TH>Comercial</TH>
            <TH right>Ventas comp.</TH>
            <TH right>Pizarra 1</TH>
            <TH right>Pizarra 2 real</TH>
            <TH right>ADW</TH>
            <TH right>Pts ADW</TH>
            <TH right>RNS</TH>
            <TH right>Pts RNS</TH>
            <TH right>Pizarra 2 aj.</TH>
            <TH right>% concurso</TH>
            <TH right>Concurso €</TH>
            <TH right>Premio 499+</TH>
            <TH right>Rappel bonus</TH>
            <TH right>Rappel indiv.</TH>
            <TH right>Super pareja</TH>
            <TH right>Total esperado</TH>
            <TH right>Com. declarada</TH>
            <TH right>Diferencia</TH>
            <TH>Estado</TH>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {data.map((r) => (
            <tr key={r.comercial} className="hover:bg-slate-50">
              <TD className="font-medium text-slate-900">{r.comercial}</TD>
              <TD right>{formatNumber(r.ventas_computables_totales)}</TD>
              <TD right>{formatNumber(r.pizarra_1_final)}</TD>
              <TD right>{formatNumber(r.pizarra_2_real)}</TD>
              <TD right>{formatNumber(r.adw_computables)}</TD>
              <TD right className="font-medium text-brand-700">
                {formatNumber(r.puntos_adw_pizarra_2)}
              </TD>
              <TD right>{formatNumber(r.rns_computables)}</TD>
              <TD right className="font-medium text-brand-700">
                {formatNumber(r.puntos_rns_pizarra_2)}
              </TD>
              <TD right className="font-semibold">
                {formatNumber(r.pizarra_2_ajustada)}
              </TD>
              <TD right>{formatPercent(r.porcentaje_concurso)}</TD>
              <TD right>{formatCurrency(r.importe_concurso_obtenido)}</TD>
              <TD right>{formatCurrency(r.premio_ventas_nuevas_499)}</TD>
              <TD right>{formatCurrency(r.rappel_bonus_general)}</TD>
              <TD right>{formatCurrency(r.rappel_individual)}</TD>
              <TD right>{formatCurrency(r.super_concurso_pareja)}</TD>
              <TD right className="font-semibold text-slate-900">
                {formatCurrency(r.total_esperado)}
              </TD>
              <TD right>
                {r.comision_declarada === undefined
                  ? "—"
                  : formatCurrency(r.comision_declarada)}
              </TD>
              <TD right className={`font-medium ${diffClass(r.diferencia)}`}>
                {r.diferencia === undefined ? "—" : formatCurrency(r.diferencia)}
              </TD>
              <TD>
                <EstadoBadge estado={r.estado} />
              </TD>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
