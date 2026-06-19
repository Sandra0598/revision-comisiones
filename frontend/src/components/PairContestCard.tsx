import type { PairContestSummary } from "../types/commission";
import { Card } from "./Layout";
import { formatCurrency, formatNumber, formatPercent } from "../utils/formatters";

interface PairContestCardProps {
  pareja: PairContestSummary;
}

function Stat({
  label,
  value,
  emphasis,
}: {
  label: string;
  value: React.ReactNode;
  emphasis?: boolean;
}) {
  return (
    <div className="rounded-lg bg-slate-50 px-3 py-2 ring-1 ring-slate-100">
      <div className="text-xs text-slate-500">{label}</div>
      <div
        className={`mt-0.5 ${
          emphasis ? "text-base font-bold text-brand-700" : "text-sm font-medium text-slate-800"
        }`}
      >
        {value}
      </div>
    </div>
  );
}

export default function PairContestCard({ pareja }: PairContestCardProps) {
  return (
    <Card
      title="Super concurso de pareja · Eva + Sara"
      subtitle="Cálculo conjunto del concurso de pareja"
      right={
        <span
          className={`inline-flex rounded-full px-3 py-1 text-sm font-semibold ring-1 ${
            pareja.aplica_pareja
              ? "bg-green-100 text-green-800 ring-green-200"
              : "bg-slate-100 text-slate-600 ring-slate-200"
          }`}
        >
          {pareja.aplica_pareja ? "Aplica" : "No aplica"}
        </span>
      }
    >
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
        <Stat
          label="Ventas computables Eva"
          value={formatNumber(pareja.ventas_computables_eva)}
        />
        <Stat
          label="Ventas computables Sara"
          value={formatNumber(pareja.ventas_computables_sara)}
        />
        <Stat
          label="Ventas brutas pareja"
          value={formatNumber(pareja.ventas_brutas_pareja)}
        />
        <Stat
          label="Ventas obligatorias restadas"
          value={`− ${formatNumber(pareja.ventas_obligatorias_restadas)}`}
        />
        <Stat
          label="Ventas válidas pareja"
          value={formatNumber(pareja.ventas_validas_pareja)}
          emphasis
        />
        <Stat
          label="% concurso Eva"
          value={formatPercent(pareja.porcentaje_concurso_eva)}
        />
        <Stat
          label="% concurso Sara"
          value={formatPercent(pareja.porcentaje_concurso_sara)}
        />
        <Stat label="Nivel pareja actual" value={pareja.nivel_pareja_actual} />
        <Stat
          label="Mes consecutivo pareja"
          value={String(pareja.mes_consecutivo_pareja)}
        />
        <Stat
          label="Premio por persona"
          value={formatCurrency(pareja.premio_por_persona)}
          emphasis
        />
        <Stat label="Autorización Raúl" value={pareja.autorizacion_raul} />
        <Stat
          label="Aplica pareja"
          value={pareja.aplica_pareja ? "Sí" : "No"}
        />
      </div>

      {/* Importes finales por persona */}
      <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div className="rounded-lg border border-brand-100 bg-brand-50 px-4 py-3">
          <div className="text-xs uppercase tracking-wide text-brand-600">
            Importe final Eva (super concurso)
          </div>
          <div className="mt-0.5 text-lg font-bold text-brand-700">
            {formatCurrency(pareja.importe_final_eva)}
          </div>
        </div>
        <div className="rounded-lg border border-brand-100 bg-brand-50 px-4 py-3">
          <div className="text-xs uppercase tracking-wide text-brand-600">
            Importe final Sara (super concurso)
          </div>
          <div className="mt-0.5 text-lg font-bold text-brand-700">
            {formatCurrency(pareja.importe_final_sara)}
          </div>
        </div>
      </div>

      {pareja.alerta && (
        <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          <span className="font-semibold">Alerta: </span>
          {pareja.alerta}
        </div>
      )}

      <p className="mt-4 rounded-lg bg-slate-50 px-4 py-3 text-sm text-slate-600">
        <span className="font-semibold text-slate-700">Importante: </span>
        Eva y Sara tienen pestañas y comisiones separadas. El super concurso de
        pareja se calcula una vez, pero el importe se suma individualmente a cada
        una.
      </p>
    </Card>
  );
}
