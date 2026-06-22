"""Birds Eye View: month-by-month post analysis.

For each calendar month in range we explain *why* impressions rose or fell, then
break down the highest-reaching posts (what made them boom) and the
lowest-reaching ones (what likely went wrong) using deterministic, evidence-based
heuristics. Benchmarks like "best day" / "best format" / "high-reach hashtags"
come from the shared :mod:`content_stats`, so this view never contradicts the
Insights playbook.
"""
from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import date

from sqlalchemy.orm import Session

from app.core.dates import DateRange
from app.insights import text_utils as T
from app.insights.content_stats import ContentStats, compute_content_stats
from app.models.post import Post
from app.repositories.post_repository import PostRepository
from app.schemas.birdseye import (
    AnalyzedPost,
    BirdsEyeResponse,
    HashtagStat,
    PeriodAnalysis,
)

_MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
_DOW = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
_LONG_POST = 2200       # chars; very long bodies tend to underperform
_SHORT_POST = 120
_MANY_HASHTAGS = 10


class BirdsEyeService:
    def __init__(self, db: Session) -> None:
        self.posts = PostRepository(db)

    def analyze(self, rng: DateRange) -> BirdsEyeResponse:
        posts = [p for p in self.posts.range(rng.start, rng.end) if p.posted_at]
        # Global benchmarks shared with the Insights playbook (cohesion).
        stats = compute_content_stats(posts)

        # Month-by-month
        by_month: dict[str, list[Post]] = defaultdict(list)
        for p in posts:
            by_month[f"{p.posted_at.year}-{p.posted_at.month:02d}"].append(p)

        months_sorted = sorted(by_month)  # ascending, for prev-month deltas
        month_totals = {m: sum(p.impressions for p in ps) for m, ps in by_month.items()}

        month_analyses: list[PeriodAnalysis] = []
        for i, m in enumerate(months_sorted):
            prev_total = month_totals[months_sorted[i - 1]] if i > 0 else None
            month_analyses.append(self._analyze_period(m, by_month[m], prev_total, stats, is_quarter=False))
        month_analyses.reverse()  # newest first for display

        # Quarter-by-quarter
        by_quarter: dict[str, list[Post]] = defaultdict(list)
        for p in posts:
            q = (p.posted_at.month - 1) // 3 + 1
            by_quarter[f"{p.posted_at.year}-Q{q}"].append(p)

        quarters_sorted = sorted(by_quarter)  # ascending, for prev-quarter deltas
        quarter_totals = {q: sum(p.impressions for p in ps) for q, ps in by_quarter.items()}

        quarter_analyses: list[PeriodAnalysis] = []
        for i, q in enumerate(quarters_sorted):
            prev_total = quarter_totals[quarters_sorted[i - 1]] if i > 0 else None
            quarter_analyses.append(self._analyze_period(q, by_quarter[q], prev_total, stats, is_quarter=True))
        quarter_analyses.reverse()  # newest first for display

        return BirdsEyeResponse(months=month_analyses, quarters=quarter_analyses)

    # --- per period ---
    def _analyze_period(
        self, period: str, posts: list[Post], prev_total: float | None, stats: ContentStats, is_quarter: bool
    ) -> PeriodAnalysis:
        impressions = [p.impressions for p in posts]
        total = float(sum(impressions))
        avg = total / len(posts)
        median = float(statistics.median(impressions))

        ranked = sorted(posts, key=lambda p: p.impressions, reverse=True)

        # Split into top / low without overlap; keep a contrast even in small months.
        n = len(ranked)
        top_k = min(3, (n + 1) // 2) if n > 1 else n
        low_k = min(3, n - top_k)
        top = ranked[:top_k]
        low = list(reversed(ranked[n - low_k:])) if low_k > 0 else []

        top_analyzed = [self._boom(p, median, stats) for p in top]
        low_analyzed = [self._mistakes(p, median, stats) for p in low]

        change_pct = (total - prev_total) / prev_total * 100 if prev_total else None
        narrative = self._narrative(posts, ranked, total, prev_total, change_pct, is_quarter)

        if is_quarter:
            y, q = period.split("-")
            label = f"{q} {y}"
        else:
            y, mo = period.split("-")
            label = f"{_MONTHS[int(mo) - 1]} {y}"

        return PeriodAnalysis(
            period=period,
            label=label,
            posts=len(posts),
            total_impressions=total,
            avg_impressions=avg,
            median_impressions=median,
            prev_period_impressions=prev_total,
            impressions_change_pct=change_pct,
            trend_narrative=narrative,
            top_posts=top_analyzed,
            low_posts=low_analyzed,
            trending_hashtags=self._trending_hashtags(posts),
        )

    # --- post factor builders (benchmarks are GLOBAL via ``stats``) ---
    def _boom(self, p, median, stats: ContentStats) -> AnalyzedPost:
        tags = T.extract_hashtags(p.title)
        factors: list[str] = []
        mult = (p.impressions / median) if median else None
        if mult and mult >= 1.2:
            factors.append(f"Reached {mult:.1f}x the month's median post ({p.impressions:,} impressions).")
        if p.engagement_rate is not None and p.engagement_rate >= stats.avg_engagement and p.engagement_rate > 0:
            factors.append(
                f"Above-average {p.engagement_rate*100:.1f}% engagement; early reactions push reach through the feed algorithm."
            )
        if stats.best_format and p.post_type and p.post_type == stats.best_format:
            factors.append(f"Used your best-performing format, {stats.best_format}.")
        hit_tags = [t for t in tags if t in stats.strong_hashtags]
        if hit_tags:
            factors.append("Carried your high-reach hashtags: " + ", ".join("#" + t for t in hit_tags[:5]) + ".")
        if p.posted_at and stats.best_weekday is not None and p.posted_at.weekday() == stats.best_weekday:
            factors.append(f"Posted on {stats.best_weekday_name}, your strongest day for reach overall.")
        people = T.extract_tagged_people(p.title)
        if people:
            factors.append("Tagged collaborators (" + ", ".join(people[:4]) + "), extending reach into their networks.")
        topics = T.extract_keywords(p.title, limit=4)
        if topics:
            factors.append("Resonant topic: " + ", ".join(topics) + "; relatable and shareable for your audience.")
        if T.has_question(p.title):
            factors.append("Opens with a question or hook that invites comments.")
        if not factors:
            factors.append(f"Solid reach at {p.impressions:,} impressions.")
        return self._to_analyzed(p, median, tags, factors)

    def _mistakes(self, p, median, stats: ContentStats) -> AnalyzedPost:
        tags = T.extract_hashtags(p.title)
        factors: list[str] = []
        mult = (p.impressions / median) if median else None
        if mult is not None and mult < 1.0:
            factors.append(f"Under-reached at {p.impressions:,}, only {mult:.0%} of the month's median.")
        if not tags:
            factors.append("No hashtags, so it missed topic and discovery feeds; add 3 to 5 relevant ones.")
        elif len(tags) > _MANY_HASHTAGS:
            factors.append(f"Hashtag overload ({len(tags)}) reads as spammy; trim to 3 to 5 focused tags.")
        if T.has_link(p.title):
            factors.append("Has an external link in the body; LinkedIn suppresses outbound-link reach, so put it in the first comment instead.")
        length = T.char_length(p.title)
        if length > _LONG_POST:
            factors.append(f"Very long ({length:,} chars); a weak hook risks losing readers before they engage.")
        elif 0 < length < _SHORT_POST:
            factors.append(f"Too thin ({length} chars); little for the algorithm or readers to latch onto.")
        if stats.best_format and p.post_type and p.post_type != stats.best_format:
            factors.append(f"Format '{p.post_type}' trails your strongest format, '{stats.best_format}'.")
        if (
            p.posted_at and stats.best_weekday is not None
            and p.posted_at.weekday() != stats.best_weekday
        ):
            factors.append(f"Posted on {_DOW[p.posted_at.weekday()]}; {stats.best_weekday_name} reaches more for you overall.")
        if not T.extract_tagged_people(p.title):
            factors.append("No people tagged; tagging relevant collaborators can extend reach into their networks.")
        if p.engagement_rate is not None and stats.avg_engagement > 0 and p.engagement_rate < stats.avg_engagement:
            factors.append(f"Low {p.engagement_rate*100:.1f}% engagement gave the algorithm little signal to expand reach.")
        if not factors:
            factors.append("No standout issue; simply lighter reach this month.")
        return self._to_analyzed(p, median, tags, factors)

    @staticmethod
    def _to_analyzed(p, median, tags, factors) -> AnalyzedPost:
        return AnalyzedPost(
            post_url=p.post_url,
            hook=T.hook(p.title) or p.post_url,
            post_type=p.post_type,
            posted_at=p.posted_at.date() if p.posted_at else None,
            impressions=p.impressions,
            engagement_rate=p.engagement_rate,
            reach_multiple=round(p.impressions / median, 2) if median else None,
            hashtags=tags[:8],
            factors=factors,
        )

    @staticmethod
    def _trending_hashtags(posts: list[Post]) -> list[HashtagStat]:
        agg: dict[str, list[int]] = defaultdict(list)
        for p in posts:
            for t in T.extract_hashtags(p.title):
                agg[t].append(p.impressions)
        stats = [
            HashtagStat(tag=t, uses=len(imps), avg_impressions=sum(imps) / len(imps))
            for t, imps in agg.items()
        ]
        stats.sort(key=lambda s: (s.uses, s.avg_impressions), reverse=True)
        return stats[:8]

    @staticmethod
    def _narrative(posts, ranked, total, prev_total, change_pct, is_quarter: bool = False) -> str:
        n = len(posts)
        top = ranked[0] if ranked else None
        top_share = (top.impressions / total) if (top and total) else 0.0
        period_name = "quarter" if is_quarter else "month"

        if prev_total is None:
            base = f"First {period_name} in view: {n} post(s) drew {total:,.0f} impressions."
        elif change_pct is None or abs(change_pct) < 5:
            base = f"Impressions held roughly flat ({total:,.0f}) versus the prior {period_name}."
        elif change_pct > 0:
            base = f"Impressions rose {change_pct:.0f}% to {total:,.0f}."
        else:
            base = f"Impressions fell {abs(change_pct):.0f}% to {total:,.0f}."

        if top and top_share >= 0.4:
            driver = (
                f' Largely driven by one standout post ("{T.hook(top.title, max_chars=60)}") '
                f"at {top.impressions:,} impressions, {top_share:.0%} of the {period_name}."
            )
        elif prev_total is not None and change_pct is not None and change_pct < -5:
            driver = " Reach was spread thin: no breakout post and softer per-post performance."
        else:
            avg = total / n if n else 0
            driver = f" Reach was steady across {n} posts (avg {avg:,.0f} each)."
        return base + driver
