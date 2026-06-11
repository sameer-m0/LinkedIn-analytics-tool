import { CategoryBarChart } from "../charts/CategoryBarChart";
import { TimeSeriesChart } from "../charts/TimeSeriesChart";
import { Card, StateWrapper } from "../components/Card";
import { useFetch } from "../hooks/useFetch";
import { useRange } from "../hooks/useRange";
import { api } from "../services/api";
import { formatNumber, formatRate } from "../utils/format";

export function ContentPage() {
  const { query } = useRange();
  const { data, loading, error } = useFetch(() => api.content(query), [JSON.stringify(query)]);

  return (
    <StateWrapper loading={loading} error={error} empty={!!data && data.posts.length === 0}>
      {data && (
        <div className="space-y-6">
          <Card title="Impressions over time (with post markers)">
            <TimeSeriesChart
              serieses={[{ series: data.impressions_over_time, color: "#0a66c2", name: "Impressions" }]}
              markers={data.posts.filter((p) => p.date).map((p) => ({ date: p.date as string }))}
            />
          </Card>

          <Card title="Engagement rate over time (%)">
            <TimeSeriesChart serieses={[{ series: data.engagement_over_time, color: "#f5a623", name: "Engagement %" }]} />
          </Card>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            <Card title="Avg engagement by post type">
              <CategoryBarChart data={data.by_post_type} percent />
            </Card>
            <Card title="Avg impressions by day of week">
              <CategoryBarChart data={data.by_day_of_week} />
            </Card>
            <Card title="Avg impressions by hour bucket">
              <CategoryBarChart data={data.by_hour_bucket} />
            </Card>
          </div>

          <Card title="Posts">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b text-xs uppercase tracking-wide text-slate-400">
                    <th className="py-2 pr-3">Date</th>
                    <th className="py-2 pr-3">Type</th>
                    <th className="py-2 pr-3 text-right">Impressions</th>
                    <th className="py-2 pr-3 text-right">CTR</th>
                    <th className="py-2 pr-3 text-right">Eng. Rate</th>
                    <th className="py-2 pr-3 text-right">Reactions</th>
                    <th className="py-2 pr-3 text-right">Comments</th>
                    <th className="py-2 pr-3 text-right">Reposts</th>
                  </tr>
                </thead>
                <tbody>
                  {data.posts.map((p) => (
                    <tr key={p.post_url} className="border-b last:border-0 hover:bg-slate-50">
                      <td className="py-2 pr-3 text-slate-500">{p.date || "—"}</td>
                      <td className="py-2 pr-3">{p.post_type || "—"}</td>
                      <td className="py-2 pr-3 text-right">{formatNumber(p.impressions)}</td>
                      <td className="py-2 pr-3 text-right">{formatRate(p.ctr)}</td>
                      <td className="py-2 pr-3 text-right">{formatRate(p.engagement_rate)}</td>
                      <td className="py-2 pr-3 text-right">{formatNumber(p.reactions)}</td>
                      <td className="py-2 pr-3 text-right">{formatNumber(p.comments)}</td>
                      <td className="py-2 pr-3 text-right">{formatNumber(p.reposts)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}
    </StateWrapper>
  );
}
