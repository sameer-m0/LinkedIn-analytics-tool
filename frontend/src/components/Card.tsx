import type { ReactNode } from "react";

export function Card({ title, children, className = "" }: { title?: string; children: ReactNode; className?: string }) {
  return (
    <div className={`rounded-xl border border-slate-200 bg-white p-4 shadow-sm ${className}`}>
      {title && <h3 className="mb-3 text-sm font-semibold text-slate-600">{title}</h3>}
      {children}
    </div>
  );
}

export function StateWrapper({
  loading,
  error,
  empty,
  children,
}: {
  loading: boolean;
  error: string | null;
  empty?: boolean;
  children: ReactNode;
}) {
  if (loading) return <div className="p-6 text-sm text-slate-400">Loading…</div>;
  if (error) return <div className="p-6 text-sm text-rose-600">Error: {error}</div>;
  if (empty) return <div className="p-6 text-sm text-slate-400">No data for this period. Upload an export to get started.</div>;
  return <>{children}</>;
}
