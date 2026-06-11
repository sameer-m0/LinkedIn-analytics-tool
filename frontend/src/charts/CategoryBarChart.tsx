import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { CategoryValue } from "../types";

const PALETTE = ["#0a66c2", "#378fe9", "#5fb0f5", "#71c5c8", "#f5a623", "#e06c75", "#9b59b6"];

export function CategoryBarChart({
  data,
  horizontal = false,
  height = 260,
  percent = false,
}: {
  data: CategoryValue[];
  horizontal?: boolean;
  height?: number;
  percent?: boolean;
}) {
  if (!data.length) return <div className="p-4 text-sm text-slate-400">No data.</div>;
  const fmt = (v: number) => (percent ? `${(v * 100).toFixed(1)}%` : v.toLocaleString());
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout={horizontal ? "vertical" : "horizontal"} margin={{ left: horizontal ? 40 : -8, right: 16 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#eef2f7" />
        {horizontal ? (
          <>
            <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={fmt} />
            <YAxis type="category" dataKey="category" tick={{ fontSize: 11 }} width={120} />
          </>
        ) : (
          <>
            <XAxis dataKey="category" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} tickFormatter={fmt} />
          </>
        )}
        <Tooltip formatter={(v: number) => fmt(v)} />
        <Bar dataKey="value" radius={[4, 4, 0, 0]}>
          {data.map((_, i) => (
            <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
