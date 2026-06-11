import type { KPI } from "../types";
import { deltaClass, deltaLabel, formatNumber, formatPercent } from "../utils/format";
import { Sparkline } from "./Sparkline";

export function KpiCard({ kpi }: { kpi: KPI }) {
  const display =
    kpi.value === null ? "—" : kpi.unit === "percent" ? formatPercent(kpi.value) : formatNumber(kpi.value);
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-400">{kpi.label}</p>
          <p className="mt-1 text-2xl font-semibold text-slate-800">{display}</p>
        </div>
        <span className={`text-xs font-semibold ${deltaClass(kpi.delta_pct)}`}>{deltaLabel(kpi.delta_pct)}</span>
      </div>
      <div className="mt-2">
        <Sparkline data={kpi.sparkline} />
      </div>
    </div>
  );
}
