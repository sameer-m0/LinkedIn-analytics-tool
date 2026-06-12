import type { ReactNode } from "react";
import { Card, StateWrapper } from "../components/Card";
import { useFetch } from "../hooks/useFetch";
import { useRange } from "../hooks/useRange";
import { api } from "../services/api";
import type { Insight, PlaybookItem } from "../types";

const PLAYBOOK_ICON: Record<string, string> = {
  best_time: "🕒",
  best_format: "🎬",
  hashtags: "#️⃣",
  topics: "💡",
  tag: "🏷️",
  hook: "✍️",
};

function PlaybookCard({ item }: { item: PlaybookItem }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-center gap-2">
        <span className="text-lg">{PLAYBOOK_ICON[item.key] || "✅"}</span>
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{item.title}</p>
      </div>
      <p className="mt-1 text-lg font-semibold text-slate-800">{item.headline}</p>
      <p className="mt-1 text-sm text-slate-600">{item.detail}</p>
      {item.items.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {item.items.map((c) => (
            <span key={c} className="rounded-full bg-brand-light px-2 py-0.5 text-xs text-brand-dark">{c}</span>
          ))}
        </div>
      )}
      <p className="mt-2 text-[11px] text-slate-400">{item.evidence}</p>
    </div>
  );
}

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
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="font-semibold text-slate-800">{insight.title}</h3>
      <p className="mt-1 text-sm text-slate-600">{insight.evidence}</p>
      <div className="mt-2 flex gap-2 rounded-lg bg-brand-light/60 p-2">
        <span>💡</span>
        <p className="text-sm font-medium text-slate-800">{insight.recommendation}</p>
      </div>
      <div className="mt-3 grid grid-cols-1 gap-1.5 sm:grid-cols-2">
        <ScoreBar label="Impact" value={insight.impact_score} color="#0a66c2" />
        <ScoreBar label="Confidence" value={insight.confidence_score * 100} color="#71c5c8" />
      </div>
    </div>
  );
}

function SectionTitle({ children, hint }: { children: ReactNode; hint?: string }) {
  return (
    <div className="mb-3">
      <h2 className="text-base font-semibold text-slate-800">{children}</h2>
      {hint && <p className="text-xs text-slate-400">{hint}</p>}
    </div>
  );
}

export function InsightsPage() {
  const { query } = useRange();
  const { data, loading, error } = useFetch(() => api.insights(query), [JSON.stringify(query)]);

  return (
    <StateWrapper loading={loading} error={error}>
      {data && (
        <div className="space-y-8">
          <section>
            <SectionTitle hint="Learned from your past posts — apply these to your next post.">
              Your Content Playbook
            </SectionTitle>
            {data.playbook.length ? (
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {data.playbook.map((p) => <PlaybookCard key={p.key} item={p} />)}
              </div>
            ) : (
              <Card><p className="text-sm text-slate-400">Upload more content to learn a playbook (need at least 3 posts).</p></Card>
            )}
          </section>

          <section>
            <SectionTitle hint={`Evidence-backed for ${data.range_start} → ${data.range_end}. No evidence, no recommendation.`}>
              Recommendations
            </SectionTitle>
            {data.insights.length ? (
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                {data.insights.map((i) => <InsightCard key={i.rule_id} insight={i} />)}
              </div>
            ) : (
              <Card><p className="text-sm text-slate-400">No rule-based recommendations fired for this period. Widen the date range or upload more data.</p></Card>
            )}
          </section>
        </div>
      )}
    </StateWrapper>
  );
}
