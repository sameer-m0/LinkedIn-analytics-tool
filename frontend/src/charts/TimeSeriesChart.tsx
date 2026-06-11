import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Series } from "../types";

export interface SeriesConfig {
  series: Series;
  color: string;
  name: string;
}

export interface Marker {
  date: string;
  label?: string;
}

/** Multi-series line chart merged on the date axis, with optional markers. */
export function TimeSeriesChart({
  serieses,
  markers = [],
  height = 280,
}: {
  serieses: SeriesConfig[];
  markers?: Marker[];
  height?: number;
}) {
  type Row = Record<string, string | number> & { date: string };
  const byDate: Record<string, Row> = {};
  serieses.forEach((cfg) => {
    cfg.series.points.forEach((p) => {
      if (!byDate[p.date]) byDate[p.date] = { date: p.date };
      byDate[p.date][cfg.name] = p.value;
    });
  });
  const data = Object.values(byDate).sort((a, b) => a.date.localeCompare(b.date));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: -8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#eef2f7" />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} minTickGap={24} />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        {markers.map((m, i) => (
          <ReferenceLine key={i} x={m.date} stroke="#94a3b8" strokeDasharray="2 2" />
        ))}
        {serieses.map((cfg) => (
          <Line
            key={cfg.name}
            type="monotone"
            dataKey={cfg.name}
            stroke={cfg.color}
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
