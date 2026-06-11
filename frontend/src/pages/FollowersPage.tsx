import { CategoryBarChart } from "../charts/CategoryBarChart";
import { TimeSeriesChart } from "../charts/TimeSeriesChart";
import { Card, StateWrapper } from "../components/Card";
import { useFetch } from "../hooks/useFetch";
import { useRange } from "../hooks/useRange";
import { api } from "../services/api";

const DEMO_LABELS: Record<string, string> = {
  job_function: "Job Function",
  seniority: "Seniority",
  industry: "Industry",
  location: "Location",
  company_size: "Company Size",
};

export function FollowersPage() {
  const { query } = useRange();
  const { data, loading, error } = useFetch(() => api.followers(query), [JSON.stringify(query)]);

  return (
    <StateWrapper loading={loading} error={error} empty={!!data && data.daily.points.length === 0}>
      {data && (
        <div className="space-y-6">
          <Card title="Daily new followers & 7-day rolling average">
            <TimeSeriesChart
              serieses={[
                { series: data.daily, color: "#0a66c2", name: "Daily" },
                { series: data.rolling_7d, color: "#f5a623", name: "7d avg" },
              ]}
            />
          </Card>

          <Card title="Cumulative followers">
            <TimeSeriesChart serieses={[{ series: data.cumulative, color: "#0a66c2", name: "Cumulative" }]} />
          </Card>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {Object.entries(data.demographics).map(([dim, values]) => (
              <Card key={dim} title={DEMO_LABELS[dim] || dim}>
                <CategoryBarChart data={values} horizontal />
              </Card>
            ))}
          </div>
        </div>
      )}
    </StateWrapper>
  );
}
