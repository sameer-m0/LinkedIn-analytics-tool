export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value);
}

export function formatPercent(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined) return "—";
  return `${value.toFixed(digits)}%`;
}

// engagement/ctr are stored as fractions (0.05 == 5%).
export function formatRate(fraction: number | null | undefined, digits = 2): string {
  if (fraction === null || fraction === undefined) return "—";
  return `${(fraction * 100).toFixed(digits)}%`;
}

export function deltaClass(delta: number | null | undefined): string {
  if (delta === null || delta === undefined) return "text-slate-400";
  return delta >= 0 ? "text-emerald-600" : "text-rose-600";
}

export function deltaLabel(delta: number | null | undefined): string {
  if (delta === null || delta === undefined) return "—";
  const sign = delta >= 0 ? "▲" : "▼";
  return `${sign} ${Math.abs(delta).toFixed(1)}%`;
}
