import type { ReactNode } from "react";

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-full">
      <header className="bg-brand-600 text-white shadow-soft">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
            Revisión de Comisiones Comerciales
          </h1>
          <p className="mt-1 text-brand-100">
            Sube el Excel mensual, revisa concursos, rappels, bonus y descarga el
            informe final.
          </p>
        </div>
      </header>
      <main className="mx-auto max-w-7xl space-y-6 px-4 py-8 sm:px-6 lg:px-8">
        {children}
      </main>
      <footer className="mx-auto max-w-7xl px-4 pb-10 pt-2 text-center text-xs text-slate-400 sm:px-6 lg:px-8">
        Revisión de comisiones — informe del mes anterior.
      </footer>
    </div>
  );
}

/** Card reutilizable con sombra suave. */
export function Card({
  title,
  subtitle,
  children,
  right,
}: {
  title?: string;
  subtitle?: string;
  children: ReactNode;
  right?: ReactNode;
}) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white shadow-soft">
      {(title || right) && (
        <div className="flex items-start justify-between gap-4 border-b border-slate-100 px-5 py-4">
          <div>
            {title && (
              <h2 className="text-lg font-semibold text-slate-800">{title}</h2>
            )}
            {subtitle && (
              <p className="mt-0.5 text-sm text-slate-500">{subtitle}</p>
            )}
          </div>
          {right}
        </div>
      )}
      <div className="p-5">{children}</div>
    </section>
  );
}
