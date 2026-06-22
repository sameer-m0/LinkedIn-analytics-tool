import { useState } from "react";
import { Card, StateWrapper } from "../components/Card";
import { useFetch } from "../hooks/useFetch";
import { useRange } from "../hooks/useRange";
import { api } from "../services/api";
import type { PostCopywritingAnalysis } from "../types";
import { formatNumber, formatRate } from "../utils/format";

// Helper to render tone badge with corresponding emoji and style
function ToneBadge({ tone }: { tone: string }) {
  const tonesMap: Record<string, { label: string; style: string }> = {
    Storytelling: { label: "Storytelling 📖", style: "bg-indigo-50 text-indigo-700 ring-indigo-600/10" },
    Educational: { label: "Educational 💡", style: "bg-emerald-50 text-emerald-700 ring-emerald-600/10" },
    Promotional: { label: "Promotional 📣", style: "bg-purple-50 text-purple-700 ring-purple-600/10" },
    Conversational: { label: "Conversational 💬", style: "bg-amber-50 text-amber-700 ring-amber-600/10" },
    Technical: { label: "Technical 💻", style: "bg-cyan-50 text-cyan-700 ring-cyan-600/10" },
    Insightful: { label: "Insightful 🎯", style: "bg-slate-50 text-slate-700 ring-slate-600/10" },
  };

  const current = tonesMap[tone] || { label: tone, style: "bg-slate-50 text-slate-700 ring-slate-600/10" };

  return (
    <span className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset ${current.style}`}>
      {current.label}
    </span>
  );
}

// Hook strength badge styling
function HookStrengthBadge({ level }: { level: string }) {
  const styles: Record<string, string> = {
    High: "bg-emerald-50 text-emerald-700 ring-emerald-600/10",
    Medium: "bg-amber-50 text-amber-700 ring-amber-600/10",
    Low: "bg-rose-50 text-rose-700 ring-rose-600/10",
  };
  return (
    <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-semibold ring-1 ring-inset ${styles[level] || styles.Medium}`}>
      {level} Hook
    </span>
  );
}

// Collapsible post body container
function CollapsibleBody({ text }: { text: string }) {
  const [expanded, setExpanded] = useState(false);
  const maxChars = 260;
  
  if (text.length <= maxChars) {
    return <p className="text-sm text-slate-700 whitespace-pre-wrap leading-relaxed">{text}</p>;
  }

  return (
    <div className="space-y-2">
      <p className="text-sm text-slate-700 whitespace-pre-wrap leading-relaxed">
        {expanded ? text : `${text.slice(0, maxChars)}...`}
      </p>
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="text-xs font-semibold text-brand hover:text-brand-dark transition"
      >
        {expanded ? "Show Less" : "Show Full Post Content"}
      </button>
    </div>
  );
}

function CopywritingCard({ p }: { p: PostCopywritingAnalysis }) {
  return (
    <Card>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-3">
        <div className="flex flex-wrap items-center gap-2">
          <ToneBadge tone={p.tone} />
          {p.post_type && (
            <span className="inline-flex items-center rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600 uppercase">
              {p.post_type}
            </span>
          )}
          {p.posted_at && <span className="text-xs text-slate-400 font-medium">{p.posted_at}</span>}
        </div>
        <div className="flex items-center gap-6">
          <div className="text-right">
            <span className="text-sm font-bold text-slate-800">{formatNumber(p.impressions)}</span>
            <p className="text-[10px] uppercase font-semibold tracking-wide text-slate-400">Impressions</p>
          </div>
          {p.engagement_rate !== null && (
            <div className="text-right">
              <span className="text-sm font-bold text-slate-800">{formatRate(p.engagement_rate)}</span>
              <p className="text-[10px] uppercase font-semibold tracking-wide text-slate-400">Eng. Rate</p>
            </div>
          )}
        </div>
      </div>

      <div className="mb-4 rounded-lg bg-slate-50/50 p-4 border border-slate-100/50">
        <CollapsibleBody text={p.title || ""} />
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {/* Left column: copywriting metrics */}
        <div className="space-y-4">
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">First Lines Hook</h3>
              <HookStrengthBadge level={p.hook_effectiveness} />
            </div>
            <p className="text-sm italic text-slate-600 bg-slate-50/20 px-3 py-2 rounded border border-dashed border-slate-200">
              "{p.hook}"
            </p>
          </div>

          <div>
            <h3 className="mb-1 text-xs font-semibold uppercase tracking-wider text-slate-400">Key Hooks & Phrases</h3>
            <ul className="space-y-1">
              {p.key_hooks.map((h, i) => (
                <li key={i} className="text-xs text-slate-700 flex gap-2">
                  <span className="text-brand">▪</span>
                  <span>{h}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Right column: qualitative feedback */}
        <div className="space-y-4">
          <div>
            <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-slate-400">What Worked Well</h3>
            <ul className="space-y-1.5">
              {p.convincing_elements.map((el, i) => (
                <li key={i} className="text-xs text-slate-700 flex items-start gap-2">
                  <span className="text-emerald-500 font-bold shrink-0">✓</span>
                  <span>{el}</span>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-slate-400">Areas of Improvement</h3>
            <ul className="space-y-1.5">
              {p.improvement_suggestions.map((sug, i) => (
                <li key={i} className="text-xs text-slate-700 flex items-start gap-2">
                  <span className="text-amber-500 font-bold shrink-0">⚠</span>
                  <span>{sug}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </Card>
  );
}

export function CopywritingLabPage() {
  const { query } = useRange();
  
  // Local filter states
  const [search, setSearch] = useState("");
  const [tone, setTone] = useState("");
  const [performanceTier, setPerformanceTier] = useState("");
  const [sortBy, setSortBy] = useState("date");
  const [sortOrder, setSortOrder] = useState("desc");

  // Build reactive request payload
  const apiQuery = {
    ...query,
    search: search.trim() || undefined,
    tone: tone || undefined,
    performance_tier: performanceTier || undefined,
    sort_by: sortBy,
    sort_order: sortOrder,
  };

  const { data, loading, error } = useFetch(
    () => api.copywriting(apiQuery),
    [JSON.stringify(apiQuery)]
  );

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-800">Copywriting Lab</h2>
        <p className="text-sm text-slate-500">
          Dissect the copy and tone of every post. Filter by performance or style to see what hooks readers and what can be polished.
        </p>
      </div>

      {/* Control panel & Filter bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex flex-wrap items-center gap-3 shrink-0">
          {/* Search */}
          <input
            type="text"
            placeholder="Search post content..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-64 rounded-lg border border-slate-200 px-3 py-1.5 text-sm placeholder-slate-400 focus:border-brand focus:outline-none"
          />

          {/* Tone Filter */}
          <select
            value={tone}
            onChange={(e) => setTone(e.target.value)}
            className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm text-slate-600 focus:border-brand focus:outline-none"
          >
            <option value="">All Tones</option>
            <option value="Storytelling">Storytelling 📖</option>
            <option value="Educational">Educational 💡</option>
            <option value="Promotional">Promotional 📣</option>
            <option value="Conversational">Conversational 💬</option>
            <option value="Technical">Technical 💻</option>
            <option value="Insightful">Insightful 🎯</option>
          </select>

          {/* Performance Tier */}
          <select
            value={performanceTier}
            onChange={(e) => setPerformanceTier(e.target.value)}
            className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm text-slate-600 focus:border-brand focus:outline-none"
          >
            <option value="">All Performance Tiers</option>
            <option value="top">Top 25% (Outperforming)</option>
            <option value="mid">Mid Tier (Average Reach)</option>
            <option value="low">Bottom 25% (Underperforming)</option>
          </select>
        </div>

        {/* Sorting controls */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Sort by</span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="rounded-lg border border-slate-200 px-2 py-1.5 text-sm text-slate-600 focus:border-brand focus:outline-none"
          >
            <option value="date">Date Published</option>
            <option value="impressions">Impressions (Reach)</option>
            <option value="engagement_rate">Engagement Rate</option>
          </select>
          <button
            type="button"
            onClick={() => setSortOrder(sortOrder === "desc" ? "asc" : "desc")}
            className="rounded-lg border border-slate-200 p-1.5 text-slate-500 hover:bg-slate-50 transition"
            title={sortOrder === "desc" ? "Descending" : "Ascending"}
          >
            {sortOrder === "desc" ? "▼" : "▲"}
          </button>
        </div>
      </div>

      {/* Posts layout */}
      <StateWrapper loading={loading} error={error} empty={!!data && data.posts.length === 0}>
        {data && (
          <div className="space-y-6">
            <div className="text-xs text-slate-400 font-medium">
              Showing {data.posts.length} analyzed post{data.posts.length !== 1 ? "s" : ""}
            </div>
            <div className="space-y-6">
              {data.posts.map((p) => (
                <CopywritingCard key={p.post_id} p={p} />
              ))}
            </div>
          </div>
        )}
      </StateWrapper>
    </div>
  );
}
