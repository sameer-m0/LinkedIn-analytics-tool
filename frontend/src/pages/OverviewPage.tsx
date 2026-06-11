import { KpiCard } from "../components/KpiCard";
import { Card, StateWrapper } from "../components/Card";
import { useFetch } from "../hooks/useFetch";
import { useRange } from "../hooks/useRange";
import { api } from "../services/api";
import { formatNumber, formatRate } from "../utils/format";

export function OverviewPage() {
  const { query } = useRange();
  const { data, loading, error } = useFetch(() => api.overview(query), [JSON.stringify(query)]);

  return (
    <StateWrapper loading={loading} error={error} empty={!!data && data.kpis.every((k) => k.value === null)}>
      {data && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {data.kpis.map((k) => (
              <KpiCard key={k.key} kpi={k} />
            ))}
          </div>

          <Card title="Top Post">
            {data.top_post ? (
              <a href={data.top_post.post_url} target="_blank" rel="noreferrer" className="block hover:bg-slate-50">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-slate-800">{data.top_post.title || data.top_post.post_url}</p>
                    <p className="text-xs text-slate-400">{data.top_post.post_type || "post"}</p>
                  </div>
                  <div className="text-right text-sm">
                    <p className="font-semibold">{formatNumber(data.top_post.impressions)} impressions</p>
                    <p className="text-slate-500">{formatRate(data.top_post.engagement_rate)} engagement</p>
                  </div>
                </div>
              </a>
            ) : (
              <p className="text-sm text-slate-400">No posts in this period.</p>
            )}
          </Card>
        </div>
      )}
    </StateWrapper>
  );
}
