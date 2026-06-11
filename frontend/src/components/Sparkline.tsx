import { Line, LineChart, ResponsiveContainer } from "recharts";

export function Sparkline({ data, color = "#0a66c2" }: { data: number[]; color?: string }) {
  if (!data || data.length < 2) return <div className="h-10" />;
  const points = data.map((value, i) => ({ i, value }));
  return (
    <div className="h-10 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={points}>
          <Line type="monotone" dataKey="value" stroke={color} strokeWidth={2} dot={false} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
