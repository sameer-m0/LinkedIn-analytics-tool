import { useRange } from "../hooks/useRange";
import type { ComparisonMode, RangePreset } from "../types";

const PRESETS: { value: RangePreset; label: string }[] = [
  { value: "last_7", label: "7D" },
  { value: "last_30", label: "30D" },
  { value: "last_90", label: "90D" },
  { value: "mtd", label: "MTD" },
  { value: "qtd", label: "QTD" },
  { value: "ytd", label: "YTD" },
  { value: "all_time", label: "All" },
];

const COMPARE: { value: ComparisonMode; label: string }[] = [
  { value: "previous_period", label: "vs Previous period" },
  { value: "same_period_last_year", label: "vs Same period last year" },
  { value: "none", label: "No comparison" },
];

export function DateRangePicker() {
  const { preset, setPreset, compare, setCompare, start, end, setCustom } = useRange();
  return (
    <div className="flex flex-wrap items-center gap-3">
      <div className="inline-flex overflow-hidden rounded-lg border border-slate-200 bg-white">
        {PRESETS.map((p) => (
          <button
            key={p.value}
            onClick={() => setPreset(p.value)}
            className={`px-3 py-1.5 text-xs font-medium transition ${
              preset === p.value ? "bg-brand text-white" : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            {p.label}
          </button>
        ))}
      </div>

      <div className="flex items-center gap-1 text-xs">
        <input
          type="date"
          value={start || ""}
          onChange={(e) => setCustom(e.target.value, end || e.target.value)}
          className="rounded border border-slate-200 px-2 py-1"
        />
        <span className="text-slate-400">→</span>
        <input
          type="date"
          value={end || ""}
          onChange={(e) => setCustom(start || e.target.value, e.target.value)}
          className="rounded border border-slate-200 px-2 py-1"
        />
      </div>

      <select
        value={compare}
        onChange={(e) => setCompare(e.target.value as ComparisonMode)}
        className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-600"
      >
        {COMPARE.map((c) => (
          <option key={c.value} value={c.value}>{c.label}</option>
        ))}
      </select>
    </div>
  );
}
