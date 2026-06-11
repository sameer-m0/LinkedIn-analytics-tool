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

          <Card title="Top Performing Posts">
            {data.top_posts && data.top_posts.length > 0 ? (
              <div className="divide-y divide-slate-100">
                {data.top_posts.map((post, idx) => (
                  <a
                    key={post.post_url}
                    href={post.post_url}
                    target="_blank"
                    rel="noreferrer"
                    className="block py-3 hover:bg-slate-50 first:pt-0 last:pb-0"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-slate-100 text-xs font-semibold text-slate-500">
                          #{idx + 1}
                        </span>
                        <div>
                          <p className="font-medium text-slate-800 line-clamp-1 max-w-lg">
                            {post.title || post.post_url}
                          </p>
                          <p className="text-xs text-slate-400">{post.post_type || "post"}</p>
                        </div>
                      </div>
                      <div className="text-right text-sm">
                        <p className="font-semibold">{formatNumber(post.impressions)} impressions</p>
                        <p className="text-slate-500">{formatRate(post.engagement_rate)} engagement</p>
                      </div>
                    </div>
                  </a>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-400">No posts in this period.</p>
            )}
          </Card>

        </div>
      )}
    </StateWrapper>
  );
}
