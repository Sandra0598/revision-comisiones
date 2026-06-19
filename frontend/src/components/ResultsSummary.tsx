import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { CommercialSummary } from "../types/commission";
import { Card } from "./Layout";
import CommercialTable from "./CommercialTable";
import { formatCurrency } from "../utils/formatters";

interface ResultsSummaryProps {
  data: CommercialSummary[];
  mes?: number;
  anio?: number;
}

const MESES = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];

export default function ResultsSummary({ data, mes, anio }: ResultsSummaryProps) {
  const totalGlobal = data.reduce((acc, r) => acc + r.total_esperado, 0);
  const periodo =
    mes && anio ? `${MESES[mes - 1] ?? mes} ${anio}` : undefined;

  const chartData = data.map((r) => ({
    name: r.comercial,
    total: Math.round(r.total_esperado * 100) / 100,
  }));

  return (
    <Card
      title="Resumen general"
      subtitle={
        periodo
          ? `Periodo revisado: ${periodo} · ${data.length} comerciales`
          : `${data.length} comerciales`
      }
      right={
        <div className="text-right">
          <div className="text-xs uppercase tracking-wide text-slate-400">
            Total esperado
          </div>
          <div className="text-xl font-bold text-brand-700">
            {formatCurrency(totalGlobal)}
          </div>
        </div>
      }
    >
      {data.length > 0 && (
        <div className="mb-6 h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip
                formatter={(value: number) => formatCurrency(value)}
                labelClassName="font-medium"
              />
              <Bar dataKey="total" fill="#1f4e78" radius={[4, 4, 0, 0]} name="Total esperado" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <CommercialTable data={data} />
    </Card>
  );
}
