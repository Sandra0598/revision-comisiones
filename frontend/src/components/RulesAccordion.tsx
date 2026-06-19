import { useState } from "react";

interface RuleProps {
  title: string;
  children: React.ReactNode;
}

function Rule({ title, children }: RuleProps) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
      <h3 className="text-sm font-semibold text-slate-800">{title}</h3>
      <div className="mt-1.5 space-y-1 text-sm text-slate-600">{children}</div>
    </div>
  );
}

function Example({ rows, total }: { rows: string[]; total: string }) {
  return (
    <div className="mt-2 inline-block rounded-md bg-white px-3 py-2 font-mono text-xs text-slate-600 ring-1 ring-slate-200">
      {rows.map((r) => (
        <div key={r}>{r}</div>
      ))}
      <div className="mt-1 border-t border-slate-200 pt-1 font-semibold text-brand-700">
        {total}
      </div>
    </div>
  );
}

export default function RulesAccordion() {
  const [open, setOpen] = useState(false);

  return (
    <section className="rounded-xl border border-slate-200 bg-white shadow-soft">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between px-5 py-4 text-left"
      >
        <div>
          <h2 className="text-lg font-semibold text-slate-800">Reglas aplicadas</h2>
          <p className="mt-0.5 text-sm text-slate-500">
            Cómo se calculan concursos, puntos, rappels y la pareja Eva + Sara.
          </p>
        </div>
        <span className="text-slate-400">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div className="grid grid-cols-1 gap-3 border-t border-slate-100 p-5 md:grid-cols-2">
          <Rule title="Comerciales revisadas">
            Solo se revisan las ventas de las <strong>8 comerciales</strong>:
            Eva, Laura, Estela, Bea, Isamar, Sara, Susana y Virginia. Las ventas
            de cualquier otra persona se ignoran.
          </Rule>

          <Rule title="Filas que se revisan">
            Solo se revisan las filas cuya columna <strong>pizarra</strong> sea{" "}
            <strong>1</strong>, <strong>2</strong>,{" "}
            <strong>Subida precio</strong>, <strong>Igual de precio</strong> o{" "}
            <strong>Bajada precio</strong>, y aquellas cuya{" "}
            <strong>categoría de venta</strong> sea <strong>Cartera</strong>. El
            resto de filas se descartan.
          </Rule>

          <Rule title="Cartera → ADW">
            Las ventas de categoría <strong>Cartera</strong> son las que cuentan
            para el cálculo de <strong>ADW</strong>: suman 1 punto a Pizarra 2 por
            cada 3 (hitos de 3).
          </Rule>

          <Rule title="Subida de precio → RNS">
            Las filas con pizarra <strong>Subida precio</strong> son las subidas
            RNS: suman 1 punto a Pizarra 2 por cada 4 (hitos de 4).
          </Rule>

          <Rule title="Igual y Bajada de precio">
            Las filas <strong>Igual de precio</strong> y{" "}
            <strong>Bajada de precio</strong> se revisan y se muestran en la
            pestaña de la comercial, pero <strong>no computan</strong> en ningún
            cálculo (ni ventas, ni pizarras, ni puntos).
          </Rule>

          <Rule title="Venta doble">
            Las ventas de <strong>859 €</strong> cuentan como{" "}
            <strong>2 ventas computables</strong>.
          </Rule>

          <Rule title="Pizarra 1">
            Pizarra 1 necesita <strong>13 ventas</strong>.
          </Rule>

          <Rule title="Pizarra 2">
            Pizarra 2 necesita <strong>12 ventas</strong>. A sus ventas reales se
            suman los puntos generados por ADW y subidas RNS.
          </Rule>

          <Rule title="Regla ADW (hitos de 3)">
            Los ADW generan puntos para Pizarra 2 únicamente en hitos de 3: la 3.ª
            ADW suma 1 punto, la 6.ª suma otro punto, la 9.ª suma otro punto, etc.
            La 4.ª y 5.ª no suman punto propio.
            <Example
              rows={[
                "1 ADW = 0",
                "2 ADW = 0",
                "3 ADW = 1",
                "4 ADW = 0",
                "5 ADW = 0",
                "6 ADW = 1",
              ]}
              total="Total con 6 ADW = 2 puntos"
            />
          </Rule>

          <Rule title="Regla RNS (hitos de 4)">
            Las subidas de precio RNS generan puntos para Pizarra 2 únicamente en
            hitos de 4: la 4.ª subida suma 1 punto, la 8.ª suma otro punto, la 12.ª
            suma otro punto, etc.
            <Example
              rows={[
                "1 RNS = 0",
                "2 RNS = 0",
                "3 RNS = 0",
                "4 RNS = 1",
                "5 RNS = 0",
                "6 RNS = 0",
                "7 RNS = 0",
                "8 RNS = 1",
              ]}
              total="Total con 8 RNS = 2 puntos"
            />
          </Rule>

          <Rule title="Tablas individuales (−25)">
            Antes de mirar cualquier tabla individual de rappel o bonus, se restan{" "}
            <strong>25 ventas obligatorias</strong> a la totalidad de ventas de la
            comercial.
            <div className="mt-2 rounded-md bg-white px-3 py-2 font-mono text-xs text-slate-600 ring-1 ring-slate-200">
              ventas válidas para tabla = ventas computables totales − 25
            </div>
          </Rule>

          <Rule title="Pareja Eva + Sara (−50)">
            Para el concurso de pareja se suman las ventas computables totales de
            Eva y Sara y se restan <strong>50 ventas obligatorias</strong>.
            <div className="mt-2 rounded-md bg-white px-3 py-2 font-mono text-xs text-slate-600 ring-1 ring-slate-200">
              ventas válidas pareja = ventas Eva + ventas Sara − 50
            </div>
          </Rule>

          <Rule title="Eva y Sara: comisiones separadas">
            Eva y Sara tienen sus comisiones por separado: cada una con su propia
            pestaña individual y su total final. En este negocio, el{" "}
            <strong>rappel en pareja sustituye al rappel individual</strong> de
            cada una, y conservan su concurso, premio 499+ y rappel bonus general.
            Si aplica, se suma a cada una el mismo importe del super concurso de
            pareja.
          </Rule>
        </div>
      )}
    </section>
  );
}
