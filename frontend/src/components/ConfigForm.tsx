import { useState } from "react";
import type { AutorizacionRaul, Config } from "../types/commission";

interface ConfigFormProps {
  config: Config;
  onChange: (config: Config) => void;
  loading?: boolean;
}

interface NumberFieldDef {
  key: keyof Config;
  label: string;
  step?: number;
  min?: number;
  help?: string;
}

const NUMBER_FIELDS: NumberFieldDef[] = [
  { key: "premio_ventas_nuevas_499", label: "Premio ventas nuevas 499+ (€)", step: 1, min: 0 },
  { key: "minimo_ventas_nuevas_499", label: "Mínimo ventas nuevas 499+", step: 1, min: 0 },
  { key: "ventas_obligatorias_individual", label: "Ventas obligatorias individual", step: 1, min: 0 },
  { key: "ventas_obligatorias_pareja", label: "Ventas obligatorias pareja", step: 1, min: 0 },
  { key: "objetivo_pizarra_1", label: "Objetivo Pizarra 1", step: 1, min: 0 },
  { key: "objetivo_pizarra_2", label: "Objetivo Pizarra 2", step: 1, min: 0 },
  { key: "referencia_frias_100", label: "Referencia frías 100%", step: 1, min: 0 },
  { key: "referencia_upselling_100", label: "Referencia upselling 100%", step: 1, min: 0 },
  { key: "equivalencia_upselling_a_fria", label: "Equivalencia upselling → fría", step: 0.1, min: 0 },
  { key: "adw_bloque_para_punto", label: "ADW: bloque para 1 punto", step: 1, min: 1 },
  { key: "rns_bloque_para_punto", label: "RNS: bloque para 1 punto", step: 1, min: 1 },
  { key: "importe_venta_doble", label: "Importe venta doble (€)", step: 1, min: 0 },
];

const MESES = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];

const labelCls = "block text-sm font-medium text-slate-600";
const inputCls =
  "mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-brand-600 focus:outline-none focus:ring-1 focus:ring-brand-600";

export default function ConfigForm({ config, onChange, loading }: ConfigFormProps) {
  const [open, setOpen] = useState(true);
  const [comercialName, setComercialName] = useState("");
  const [comercialMes, setComercialMes] = useState("1");

  function setField<K extends keyof Config>(key: K, value: Config[K]) {
    onChange({ ...config, [key]: value });
  }

  function setNumber(key: keyof Config, raw: string) {
    const value = raw === "" ? 0 : Number(raw);
    setField(key, (Number.isNaN(value) ? 0 : value) as Config[keyof Config]);
  }

  const meses = config.meses_consecutivos_individual ?? {};

  function addComercialMes() {
    const name = comercialName.trim();
    if (!name) return;
    onChange({
      ...config,
      meses_consecutivos_individual: { ...meses, [name]: comercialMes },
    });
    setComercialName("");
    setComercialMes("1");
  }

  function removeComercialMes(name: string) {
    const next = { ...meses };
    delete next[name];
    onChange({ ...config, meses_consecutivos_individual: next });
  }

  return (
    <section className="rounded-xl border border-slate-200 bg-white shadow-soft">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between px-5 py-4 text-left"
      >
        <div>
          <h2 className="text-lg font-semibold text-slate-800">Configuración</h2>
          <p className="mt-0.5 text-sm text-slate-500">
            Valores por defecto cargados del backend. Edita lo que necesites.
          </p>
        </div>
        <span className="text-slate-400">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div className="space-y-6 border-t border-slate-100 p-5">
          {/* Concurso por equipos */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {([1, 2] as const).map((n) => {
              const importeKey = (
                n === 1 ? "importe_concurso_equipo_1" : "importe_concurso_equipo_2"
              ) as keyof Config;
              const equipoKey = (n === 1 ? "equipo_1" : "equipo_2") as keyof Config;
              const miembros = (config[equipoKey] as string[] | undefined) ?? [];
              return (
                <div
                  key={n}
                  className="rounded-lg border border-brand-200 bg-brand-50/40 p-4"
                >
                  <h3 className="text-sm font-semibold text-slate-700">
                    Concurso Equipo {n}
                  </h3>
                  <label className={`${labelCls} mt-3`}>
                    Importe del concurso del equipo (€)
                  </label>
                  <input
                    type="number"
                    step={1}
                    min={0}
                    disabled={loading}
                    className={inputCls}
                    value={Number(config[importeKey] ?? 0)}
                    onChange={(e) => setNumber(importeKey, e.target.value)}
                  />
                  <label className={`${labelCls} mt-3`}>
                    Comerciales del equipo (separadas por comas)
                  </label>
                  <input
                    className={inputCls}
                    disabled={loading}
                    value={miembros.join(", ")}
                    onChange={(e) =>
                      setField(
                        equipoKey,
                        e.target.value
                          .split(",")
                          .map((s) => s.trim())
                          .filter(Boolean) as Config[keyof Config]
                      )
                    }
                  />
                  <p className="mt-1 text-xs text-slate-500">
                    El concurso de cada comercial = su % × este importe.
                  </p>
                </div>
              );
            })}
          </div>

          {/* Parámetros numéricos */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {NUMBER_FIELDS.map((f) => (
              <div key={String(f.key)}>
                <label className={labelCls} htmlFor={String(f.key)}>
                  {f.label}
                </label>
                <input
                  id={String(f.key)}
                  type="number"
                  step={f.step}
                  min={f.min}
                  disabled={loading}
                  className={inputCls}
                  value={Number(config[f.key] ?? 0)}
                  onChange={(e) => setNumber(f.key, e.target.value)}
                />
              </div>
            ))}
          </div>

          {/* Selects y toggles */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <div>
              <label className={labelCls}>Modalidad % concurso</label>
              <select
                className={inputCls}
                disabled={loading}
                value={config.modalidad_porcentaje_concurso}
                onChange={(e) =>
                  setField("modalidad_porcentaje_concurso", e.target.value)
                }
              >
                <option value="pizarra_1_y_pizarra_2">
                  Pizarra 1 y Pizarra 2
                </option>
              </select>
            </div>

            <div>
              <label className={labelCls}>Autorización Raúl</label>
              <select
                className={inputCls}
                disabled={loading}
                value={config.autorizacion_raul ?? "Pendiente"}
                onChange={(e) =>
                  setField(
                    "autorizacion_raul",
                    e.target.value as AutorizacionRaul
                  )
                }
              >
                <option value="Sí">Sí</option>
                <option value="No">No</option>
                <option value="Pendiente">Pendiente</option>
              </select>
            </div>

            <div>
              <label className={labelCls}>Nivel pareja mes anterior</label>
              <select
                className={inputCls}
                disabled={loading}
                value={config.nivel_pareja_mes_anterior ?? ""}
                onChange={(e) =>
                  setField("nivel_pareja_mes_anterior", e.target.value)
                }
              >
                <option value="">(sin nivel previo)</option>
                <option value="Baby">Baby</option>
                <option value="Junior">Junior</option>
                <option value="Senior">Senior</option>
              </select>
            </div>

            <div>
              <label className={labelCls}>Mes consecutivo pareja</label>
              <select
                className={inputCls}
                disabled={loading}
                value={String(config.mes_consecutivo_pareja ?? "")}
                onChange={(e) =>
                  setField(
                    "mes_consecutivo_pareja",
                    e.target.value === "" ? undefined : e.target.value
                  )
                }
              >
                <option value="">(no informado)</option>
                <option value="1">1.º mes</option>
                <option value="2">2.º mes</option>
                <option value="3">3.º mes</option>
                <option value="siguientes">Meses siguientes</option>
              </select>
            </div>

            <div>
              <label className={labelCls}>Mes a revisar</label>
              <select
                className={inputCls}
                disabled={loading}
                value={String(config.mes_revision ?? "")}
                onChange={(e) =>
                  setField(
                    "mes_revision",
                    e.target.value === "" ? undefined : Number(e.target.value)
                  )
                }
              >
                <option value="">(inferir del Excel)</option>
                {MESES.map((m, i) => (
                  <option key={m} value={i + 1}>
                    {m}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className={labelCls}>Año a revisar</label>
              <input
                type="number"
                step={1}
                min={2000}
                disabled={loading}
                placeholder="(inferir del Excel)"
                className={inputCls}
                value={config.anio_revision ?? ""}
                onChange={(e) =>
                  setField(
                    "anio_revision",
                    e.target.value === "" ? undefined : Number(e.target.value)
                  )
                }
              />
            </div>
          </div>

          {/* Toggles booleanos */}
          <div className="flex flex-wrap gap-6">
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                disabled={loading}
                checked={config.activar_venta_doble_859}
                onChange={(e) =>
                  setField("activar_venta_doble_859", e.target.checked)
                }
                className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-600"
              />
              Activar venta doble 859 €
            </label>
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                disabled={loading}
                checked={config.aplicar_premios_solo_si_100_concurso}
                onChange={(e) =>
                  setField(
                    "aplicar_premios_solo_si_100_concurso",
                    e.target.checked
                  )
                }
                className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-600"
              />
              Aplicar premios solo si concurso ≥ 100%
            </label>
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                disabled={loading}
                checked={config.permitir_extrapolar_rappel_bonus ?? false}
                onChange={(e) =>
                  setField("permitir_extrapolar_rappel_bonus", e.target.checked)
                }
                className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-600"
              />
              Extrapolar rappel bonus &gt; 58
            </label>
          </div>

          {/* Comerciales a revisar */}
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <h3 className="text-sm font-semibold text-slate-700">
              Comerciales a revisar
            </h3>
            <p className="mt-0.5 text-xs text-slate-500">
              Solo se revisan las ventas de estas comerciales (el resto se
              ignora). Sepáralas por comas.
            </p>
            <input
              className={inputCls}
              disabled={loading}
              value={(config.comerciales_validas ?? []).join(", ")}
              onChange={(e) =>
                setField(
                  "comerciales_validas",
                  e.target.value
                    .split(",")
                    .map((s) => s.trim())
                    .filter(Boolean)
                )
              }
            />
          </div>

          {/* Mes consecutivo individual por comercial */}
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <h3 className="text-sm font-semibold text-slate-700">
              Mes consecutivo individual por comercial (opcional)
            </h3>
            <p className="mt-0.5 text-xs text-slate-500">
              Indica el mes consecutivo de cada comercial para el rappel
              individual. Si no se informa, se asume 1.º mes.
            </p>

            <div className="mt-3 flex flex-wrap items-end gap-3">
              <div className="grow">
                <label className={labelCls}>Comercial</label>
                <input
                  className={inputCls}
                  disabled={loading}
                  placeholder="Nombre de la comercial"
                  value={comercialName}
                  onChange={(e) => setComercialName(e.target.value)}
                />
              </div>
              <div>
                <label className={labelCls}>Mes consecutivo</label>
                <select
                  className={inputCls}
                  disabled={loading}
                  value={comercialMes}
                  onChange={(e) => setComercialMes(e.target.value)}
                >
                  <option value="1">1.º mes</option>
                  <option value="2">2.º mes</option>
                  <option value="3">3.º mes</option>
                  <option value="siguientes">Meses siguientes</option>
                </select>
              </div>
              <button
                type="button"
                onClick={addComercialMes}
                disabled={loading}
                className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
              >
                Añadir
              </button>
            </div>

            {Object.keys(meses).length > 0 && (
              <ul className="mt-3 flex flex-wrap gap-2">
                {Object.entries(meses).map(([name, mes]) => (
                  <li
                    key={name}
                    className="flex items-center gap-2 rounded-full bg-white px-3 py-1 text-sm text-slate-700 shadow-sm ring-1 ring-slate-200"
                  >
                    <span className="font-medium">{name}</span>
                    <span className="text-slate-400">mes {String(mes)}</span>
                    <button
                      type="button"
                      onClick={() => removeComercialMes(name)}
                      className="text-slate-400 hover:text-red-600"
                      aria-label={`Quitar ${name}`}
                    >
                      ✕
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
