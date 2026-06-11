import { CategoryBarChart } from "../charts/CategoryBarChart";
import { TimeSeriesChart } from "../charts/TimeSeriesChart";
import { Card, StateWrapper } from "../components/Card";
import { useFetch } from "../hooks/useFetch";
import { useRange } from "../hooks/useRange";
import { api } from "../services/api";

export function VisitorsPage() {
  const { query } = useRange();
  const { data, loading, error } = useFetch(() => api.visitors(query), [JSON.stringify(query)]);

  return (
    <StateWrapper loading={loading} error={error} empty={!!data && data.page_views.points.length === 0}>
      {data && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            <Card className="lg:col-span-2" title="Page views & unique visitors">
              <TimeSeriesChart
                serieses={[
                  { series: data.page_views, color: "#0a66c2", name: "Page views" },
                  { series: data.unique_visitors, color: "#71c5c8", name: "Unique visitors" },
                ]}
              />
            </Card>
            <Card title="Followers per unique visitor">
              <div className="flex h-[280px] flex-col items-center justify-center">
                <p className="text-5xl font-bold text-brand">
                  {data.followers_per_unique_visitor !== null
                    ? data.followers_per_unique_visitor.toFixed(2)
                    : "—"}
                </p>
                <p className="mt-2 text-sm text-slate-400">followers / unique visitor</p>
              </div>
            </Card>
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card title="Section views">
              <CategoryBarChart data={data.section_views} />
            </Card>
            <Card title="Desktop vs Mobile">
              <CategoryBarChart data={data.device_split} />
            </Card>
          </div>
        </div>
      )}
    </StateWrapper>
  );
}
