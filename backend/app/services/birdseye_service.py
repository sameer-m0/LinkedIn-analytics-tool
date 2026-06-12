"""Birds Eye View: month-by-month post analysis.

For each calendar month in range we explain *why* impressions rose or fell, then
break down the highest-reaching posts (what made them boom) and the
lowest-reaching ones (what likely went wrong) using deterministic, evidence-based
heuristics over the post text + metrics. No ML, fully reproducible.
"""
from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import date

from sqlalchemy.orm import Session

from app.core.dates import DateRange
from app.insights import text_utils as T
from app.models.post import Post
from app.repositories.post_repository import PostRepository
from app.schemas.birdseye import (
    AnalyzedPost,
    BirdsEyeResponse,
    HashtagStat,
    MonthAnalysis,
)

_MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
_DOW = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
_LONG_POST = 2200       # chars; LinkedIn truncates ~210 but very long bodies underperform
_SHORT_POST = 120
_MANY_HASHTAGS = 10


def _hour_bucket(hour: int) -> str:
    if hour < 6:
        return "12–6 AM"
    if hour < 12:
        return "6 AM–12 PM"
    if hour < 18:
        return "12–6 PM"
    return "6 PM–12 AM"


class BirdsEyeService:
    def __init__(self, db: Session) -> None:
        self.posts = PostRepository(db)

    def analyze(self, rng: DateRange) -> BirdsEyeResponse:
        posts = [p for p in self.posts.range(rng.start, rng.end) if p.posted_at]
        by_month: dict[str, list[Post]] = defaultdict(list)
        for p in posts:
            by_month[f"{p.posted_at.year}-{p.posted_at.month:02d}"].append(p)

        months_sorted = sorted(by_month)  # ascending, for prev-month deltas
        month_totals = {
            m: sum(p.impressions for p in ps) for m, ps in by_month.items()
        }

        analyses: list[MonthAnalysis] = []
        for i, m in enumerate(months_sorted):
            ms = by_month[m]
            prev_total = month_totals[months_sorted[i - 1]] if i > 0 else None
            analyses.append(self._analyze_month(m, ms, prev_total))

        analyses.reverse()  # newest first for display
        return BirdsEyeResponse(months=analyses)

    # --- per month ---
    def _analyze_month(self, month: str, posts: list[Post], prev_total: float | None) -> MonthAnalysis:
        impressions = [p.impressions for p in posts]
        total = float(sum(impressions))
        avg = total / len(posts)
        median = float(statistics.median(impressions))

        ers = [p.engagement_rate for p in posts if p.engagement_rate is not None]
        avg_er = (sum(ers) / len(ers)) if ers else 0.0

        ranked = sorted(posts, key=lambda p: p.impressions, reverse=True)
        best_type = self._best_post_type(posts)
        best_day = self._best_weekday(posts)
        strong_tags = self._strong_hashtags(posts, avg)
        trending = self._trending_hashtags(posts)

        # Split into top / low without overlap. For small months we still want a
        # contrast, so top never eats more than half when that would empty low.
        n = len(ranked)
        top_k = min(3, (n + 1) // 2) if n > 1 else n
        low_k = min(3, n - top_k)
        top = ranked[:top_k]
        low = list(reversed(ranked[n - low_k:])) if low_k > 0 else []

        top_analyzed = [self._boom(p, median, avg_er, best_type, best_day, strong_tags) for p in top]
        low_analyzed = [self._mistakes(p, median, avg_er, best_type, best_day) for p in low]

        change_pct = (
            (total - prev_total) / prev_total * 100 if prev_total else None
        )
        narrative = self._narrative(posts, ranked, total, prev_total, change_pct)

        y, mo = month.split("-")
        return MonthAnalysis(
            month=month,
            label=f"{_MONTHS[int(mo) - 1]} {y}",
            posts=len(posts),
            total_impressions=total,
            avg_impressions=avg,
            median_impressions=median,
            prev_month_impressions=prev_total,
            impressions_change_pct=change_pct,
            trend_narrative=narrative,
            top_posts=top_analyzed,
            low_posts=low_analyzed,
            trending_hashtags=trending,
        )

    # --- post factor builders ---
    def _boom(self, p, median, avg_er, best_type, best_day, strong_tags) -> AnalyzedPost:
        tags = T.extract_hashtags(p.title)
        factors: list[str] = []
        mult = (p.impressions / median) if median else None
        if mult and mult >= 1.2:
            factors.append(f"Reached {mult:.1f}× the month's median post ({p.impressions:,} impressions).")
        if p.engagement_rate is not None and p.engagement_rate >= avg_er and p.engagement_rate > 0:
            factors.append(
                f"Above-average {p.engagement_rate*100:.1f}% engagement — early reactions push reach via the feed algorithm."
            )
        if best_type and p.post_type and p.post_type == best_type:
            factors.append(f"Used your best-performing format this month: {best_type}.")
        hit_tags = [t for t in tags if t in strong_tags]
        if hit_tags:
            factors.append("Carried high-reach hashtags: " + ", ".join("#" + t for t in hit_tags[:5]) + ".")
        if p.posted_at and best_day is not None and p.posted_at.weekday() == best_day:
            factors.append(f"Posted on {_DOW[best_day]} — the month's strongest day for reach.")
        topics = T.extract_keywords(p.title, limit=4)
        if topics:
            factors.append("Resonant topic: " + ", ".join(topics) + " — relatable and shareable for your audience.")
        if T.has_question(p.title):
            factors.append("Opens a question/hook that invites comments.")
        if not factors:
            factors.append(f"Solid reach at {p.impressions:,} impressions.")
        return self._to_analyzed(p, median, tags, factors)

    def _mistakes(self, p, median, avg_er, best_type, best_day) -> AnalyzedPost:
        tags = T.extract_hashtags(p.title)
        factors: list[str] = []
        mult = (p.impressions / median) if median else None
        if mult is not None and mult < 1.0:
            factors.append(f"Under-reached at {p.impressions:,} ({mult:.0%} of the month's median).")
        if not tags:
            factors.append("No hashtags — misses topic/discovery feeds. Add 3–5 relevant ones.")
        elif len(tags) > _MANY_HASHTAGS:
            factors.append(f"Hashtag overload ({len(tags)}) reads as spammy; trim to 3–5 focused tags.")
        if T.has_link(p.title):
            factors.append("Contains an external link in the body — LinkedIn suppresses reach on outbound links. Put it in the first comment instead.")
        length = T.char_length(p.title)
        if length > _LONG_POST:
            factors.append(f"Very long ({length:,} chars) — weak hook risks losing readers before they engage.")
        elif 0 < length < _SHORT_POST:
            factors.append(f"Too thin ({length} chars) — little for the algorithm or readers to latch onto.")
        if best_type and p.post_type and p.post_type != best_type:
            factors.append(f"Format '{p.post_type}' under-performed your best format ('{best_type}') this month.")
        if p.posted_at and best_day is not None and p.posted_at.weekday() != best_day:
            factors.append(f"Posted on {_DOW[p.posted_at.weekday()]}; {_DOW[best_day]} reached more this month.")
        if p.engagement_rate is not None and avg_er > 0 and p.engagement_rate < avg_er:
            factors.append(f"Low {p.engagement_rate*100:.1f}% engagement gave the algorithm little signal to expand reach.")
        if not factors:
            factors.append("No standout issue — simply lighter reach this month.")
        return self._to_analyzed(p, median, tags, factors)

    @staticmethod
    def _to_analyzed(p, median, tags, factors) -> AnalyzedPost:
        return AnalyzedPost(
            post_url=p.post_url,
            hook=T.hook(p.title) or (p.post_url),
            post_type=p.post_type,
            posted_at=p.posted_at.date() if p.posted_at else None,
            impressions=p.impressions,
            engagement_rate=p.engagement_rate,
            reach_multiple=round(p.impressions / median, 2) if median else None,
            hashtags=tags[:8],
            factors=factors,
        )

    # --- month-level helpers ---
    @staticmethod
    def _best_post_type(posts: list[Post]) -> str | None:
        by_type: dict[str, list[int]] = defaultdict(list)
        for p in posts:
            if p.post_type:
                by_type[p.post_type].append(p.impressions)
        if not by_type:
            return None
        return max(by_type, key=lambda t: sum(by_type[t]) / len(by_type[t]))

    @staticmethod
    def _best_weekday(posts: list[Post]) -> int | None:
        by_day: dict[int, list[int]] = defaultdict(list)
        for p in posts:
            if p.posted_at:
                by_day[p.posted_at.weekday()].append(p.impressions)
        if not by_day:
            return None
        return max(by_day, key=lambda d: sum(by_day[d]) / len(by_day[d]))

    @staticmethod
    def _strong_hashtags(posts: list[Post], avg: float) -> set[str]:
        agg: dict[str, list[int]] = defaultdict(list)
        for p in posts:
            for t in T.extract_hashtags(p.title):
                agg[t].append(p.impressions)
        return {t for t, imps in agg.items() if sum(imps) / len(imps) >= avg}

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
    def _narrative(posts, ranked, total, prev_total, change_pct) -> str:
        n = len(posts)
        top = ranked[0] if ranked else None
        top_share = (top.impressions / total) if (top and total) else 0.0

        if prev_total is None:
            base = f"First month in view: {n} post(s) drew {total:,.0f} impressions."
        elif change_pct is None or abs(change_pct) < 5:
            base = f"Impressions held roughly flat ({total:,.0f}) versus the prior month."
        elif change_pct > 0:
            base = f"Impressions rose {change_pct:.0f}% to {total:,.0f}."
        else:
            base = f"Impressions fell {abs(change_pct):.0f}% to {total:,.0f}."

        # Attribute the move to the most likely driver.
        if top and top_share >= 0.4:
            driver = (
                f" Largely driven by one standout post (\"{T.hook(top.title, max_chars=60)}\") "
                f"at {top.impressions:,} impressions — {top_share:.0%} of the month."
            )
        elif prev_total is not None and change_pct is not None and change_pct < -5:
            driver = " Reach was spread thin — no breakout post and softer per-post performance."
        else:
            avg = total / n if n else 0
            driver = f" Reach was steady across {n} posts (avg {avg:,.0f} each)."
        return base + driver
