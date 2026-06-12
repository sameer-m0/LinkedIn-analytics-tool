import { Card, StateWrapper } from "../components/Card";
import { useFetch } from "../hooks/useFetch";
import { useRange } from "../hooks/useRange";
import { api } from "../services/api";
import type { AnalyzedPost, MonthAnalysis } from "../types";
import { formatNumber, formatRate } from "../utils/format";

function ChangeBadge({ pct }: { pct: number | null }) {
  if (pct === null) return <span className="text-xs text-slate-400">first month</span>;
  const up = pct >= 0;
  return (
    <span className={`text-sm font-semibold ${up ? "text-emerald-600" : "text-rose-600"}`}>
      {up ? "▲" : "▼"} {Math.abs(pct).toFixed(0)}%
    </span>
  );
}

function PostBlock({ post, kind }: { post: AnalyzedPost; kind: "top" | "low" }) {
  const accent = kind === "top" ? "border-emerald-200 bg-emerald-50/40" : "border-rose-200 bg-rose-50/40";
  const dot = kind === "top" ? "text-emerald-600" : "text-rose-600";
  return (
    <div className={`rounded-lg border ${accent} p-3`}>
      <div className="flex items-start justify-between gap-3">
        <a href={post.post_url} target="_blank" rel="noreferrer" className="font-medium text-slate-800 hover:underline line-clamp-2">
          {post.hook}
        </a>
        <div className="shrink-0 text-right">
          <p className="text-sm font-semibold text-slate-800">{formatNumber(post.impressions)}</p>
          <p className="text-[11px] text-slate-400">impressions</p>
        </div>
      </div>
      <div className="mt-1 flex flex-wrap gap-x-3 gap-y-0.5 text-[11px] text-slate-500">
        {post.posted_at && <span>{post.posted_at}</span>}
        {post.reach_multiple != null && <span>{post.reach_multiple}× median</span>}
        {post.engagement_rate != null && <span>{formatRate(post.engagement_rate)} eng.</span>}
      </div>
      <ul className="mt-2 space-y-1">
        {post.factors.map((f, i) => (
          <li key={i} className="flex gap-2 text-xs text-slate-600">
            <span className={dot}>{kind === "top" ? "▲" : "✕"}</span>
            <span>{f}</span>
          </li>
        ))}
      </ul>
      {post.hashtags.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {post.hashtags.map((h) => (
            <span key={h} className="rounded bg-white px-1.5 py-0.5 text-[10px] text-brand-dark ring-1 ring-slate-200">
              #{h}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function MonthCard({ m }: { m: MonthAnalysis }) {
  return (
    <Card>
      <div className="mb-3 flex items-center justify-between border-b border-slate-100 pb-3">
        <div>
          <h2 className="text-lg font-semibold text-slate-800">{m.label}</h2>
          <p className="text-xs text-slate-400">
            {m.posts} posts · {formatNumber(m.total_impressions)} impressions · avg {formatNumber(m.avg_impressions)}
          </p>
        </div>
        <ChangeBadge pct={m.impressions_change_pct} />
      </div>

      <p className="mb-4 rounded-lg bg-slate-50 p-3 text-sm text-slate-700">{m.trend_narrative}</p>

      {m.trending_hashtags.length > 0 && (
        <div className="mb-4">
          <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">Trending hashtags this month</p>
          <div className="flex flex-wrap gap-1.5">
            {m.trending_hashtags.map((h) => (
              <span key={h.tag} className="rounded-full bg-brand-light px-2 py-0.5 text-xs text-brand-dark">
                #{h.tag} <span className="text-slate-400">· {h.uses}× · {formatNumber(h.avg_impressions)}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div>
          <p className="mb-2 text-sm font-semibold text-emerald-700">🚀 Highest reaching — what made them boom</p>
          <div className="space-y-2">
            {m.top_posts.map((p) => <PostBlock key={p.post_url} post={p} kind="top" />)}
          </div>
        </div>
        <div>
          <p className="mb-2 text-sm font-semibold text-rose-700">📉 Lowest reaching — what went wrong</p>
          <div className="space-y-2">
            {m.low_posts.length ? (
              m.low_posts.map((p) => <PostBlock key={p.post_url} post={p} kind="low" />)
            ) : (
              <p className="text-xs text-slate-400">Not enough posts this month to contrast.</p>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}

export function BirdsEyePage() {
  const { query } = useRange();
  const { data, loading, error } = useFetch(() => api.birdseye(query), [JSON.stringify(query)]);

  return (
    <StateWrapper loading={loading} error={error} empty={!!data && data.months.length === 0}>
      {data && (
        <div className="space-y-6">
          <p className="text-sm text-slate-500">
            Month-by-month read on what drove reach — why impressions moved, which posts broke out and why, and what
            held the quieter posts back. Use it to repeat the wins and avoid the misses.
          </p>
          {data.months.map((m) => <MonthCard key={m.month} m={m} />)}
        </div>
      )}
    </StateWrapper>
  );
}
