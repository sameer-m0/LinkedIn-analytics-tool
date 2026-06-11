import { Card, StateWrapper } from "../components/Card";
import { useFetch } from "../hooks/useFetch";
import { useRange } from "../hooks/useRange";
import { api } from "../services/api";
import type { Insight } from "../types";

function ScoreBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-16 text-slate-400">{label}</span>
      <div className="h-1.5 flex-1 overflow-hidden rounded bg-slate-100">
        <div className="h-full rounded" style={{ width: `${Math.min(100, value)}%`, background: color }} />
      </div>
      <span className="w-9 text-right text-slate-500">{value.toFixed(0)}</span>
    </div>
  );
}

function InsightCard({ insight }: { insight: Insight }) {
  return (
    <Card>
      <div className="mb-2 flex items-start justify-between gap-3">
        <h3 className="font-semibold text-slate-800">{insight.title}</h3>
        <span className="rounded bg-brand-light px-2 py-0.5 text-[10px] font-medium uppercase text-brand-dark">
          {insight.rule_id}
        </span>
      </div>
      <p className="text-sm text-slate-600">{insight.evidence}</p>
      <p className="mt-2 rounded-lg bg-slate-50 p-2 text-sm font-medium text-slate-800">
        💡 {insight.recommendation}
      </p>
      <div className="mt-3 space-y-1.5">
        <ScoreBar label="Impact" value={insight.impact_score} color="#0a66c2" />
        <ScoreBar label="Confidence" value={insight.confidence_score * 100} color="#71c5c8" />
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        {Object.entries(insight.supporting_metrics).map(([k, v]) => (
          <span key={k} className="rounded bg-slate-100 px-2 py-0.5 text-[11px] text-slate-500">
            {k}: {typeof v === "number" ? v.toLocaleString(undefined, { maximumFractionDigits: 3 }) : v}
          </span>
        ))}
      </div>
    </Card>
  );
}

export function InsightsPage() {
  const { query } = useRange();
  const { data, loading, error } = useFetch(() => api.insights(query), [JSON.stringify(query)]);

  return (
    <StateWrapper loading={loading} error={error}>
      {data && (
        <div>
          <p className="mb-4 text-sm text-slate-500">
            Evidence-backed recommendations for {data.range_start} → {data.range_end}. No evidence, no recommendation.
          </p>
          {data.insights.length === 0 ? (
            <Card>
              <p className="text-sm text-slate-400">
                No recommendations fired for this period. Upload more data or widen the date range.
              </p>
            </Card>
          ) : (
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              {data.insights.map((i) => (
                <InsightCard key={i.rule_id} insight={i} />
              ))}
            </div>
          )}
        </div>
      )}
    </StateWrapper>
  );
}
