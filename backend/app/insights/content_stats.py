"""Shared content statistics — a single source of truth so every tab agrees.

Birds Eye View and the Insights playbook both need "best day", "best format",
"top hashtags", "topics", and "people to tag". Computing them in two places led
to contradictions (one tab saying Monday, another Thursday). Both now derive
these from ``compute_content_stats`` over the same post set.
"""
from __future__ import annotations

import statistics
from collections import defaultdict
from dataclasses import dataclass, field

from app.insights import text_utils as T
from app.models.post import Post

_DOW = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _avg(xs) -> float:
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


@dataclass
class TagStat:
    tag: str
    uses: int
    avg_impressions: float


@dataclass
class ContentStats:
    n_posts: int = 0
    avg_impressions: float = 0.0
    median_impressions: float = 0.0
    avg_engagement: float = 0.0

    weekday_avg: dict[int, float] = field(default_factory=dict)
    best_weekday: int | None = None

    format_avg_impressions: dict[str, float] = field(default_factory=dict)
    format_avg_engagement: dict[str, float] = field(default_factory=dict)
    best_format: str | None = None

    hashtag_stats: list[TagStat] = field(default_factory=list)
    strong_hashtags: set[str] = field(default_factory=set)
    top_hashtags: list[str] = field(default_factory=list)

    topics: list[str] = field(default_factory=list)
    people: list[str] = field(default_factory=list)

    has_clock_times: bool = False

    @property
    def best_weekday_name(self) -> str | None:
        return _DOW[self.best_weekday] if self.best_weekday is not None else None

    def weekday_name(self, idx: int) -> str:
        return _DOW[idx]


def compute_content_stats(posts: list[Post]) -> ContentStats:
    posts = [p for p in posts if p.impressions is not None]
    if not posts:
        return ContentStats()

    impressions = [p.impressions for p in posts]
    ers = [p.engagement_rate for p in posts if p.engagement_rate is not None]
    stats = ContentStats(
        n_posts=len(posts),
        avg_impressions=_avg(impressions),
        median_impressions=float(statistics.median(impressions)),
        avg_engagement=_avg(ers),
    )

    # --- weekday (best day to post) ---
    by_day: dict[int, list[int]] = defaultdict(list)
    for p in posts:
        if p.posted_at:
            by_day[p.posted_at.weekday()].append(p.impressions)
            if p.posted_at.hour != 0:
                stats.has_clock_times = True
    stats.weekday_avg = {d: _avg(v) for d, v in by_day.items()}
    if stats.weekday_avg:
        stats.best_weekday = max(stats.weekday_avg, key=stats.weekday_avg.get)

    # --- format ---
    by_type_imp: dict[str, list[int]] = defaultdict(list)
    by_type_er: dict[str, list[float]] = defaultdict(list)
    for p in posts:
        if p.post_type:
            by_type_imp[p.post_type].append(p.impressions)
            if p.engagement_rate is not None:
                by_type_er[p.post_type].append(p.engagement_rate)
    stats.format_avg_impressions = {t: _avg(v) for t, v in by_type_imp.items()}
    stats.format_avg_engagement = {t: _avg(v) for t, v in by_type_er.items()}
    if len(by_type_imp) >= 2:
        stats.best_format = max(stats.format_avg_impressions, key=stats.format_avg_impressions.get)

    # --- hashtags ---
    agg: dict[str, list[int]] = defaultdict(list)
    for p in posts:
        for t in T.extract_hashtags(p.title):
            agg[t].append(p.impressions)
    stats.hashtag_stats = sorted(
        (TagStat(tag=t, uses=len(v), avg_impressions=_avg(v)) for t, v in agg.items()),
        key=lambda s: (s.avg_impressions, s.uses),
        reverse=True,
    )
    stats.strong_hashtags = {
        s.tag for s in stats.hashtag_stats if s.avg_impressions >= stats.avg_impressions
    }
    stats.top_hashtags = [
        s.tag for s in stats.hashtag_stats if s.uses >= 2 and s.avg_impressions >= stats.avg_impressions
    ][:8]

    # --- topics + people, mined from the high-reach posts ---
    ranked = sorted(posts, key=lambda p: p.impressions, reverse=True)
    top = ranked[: max(3, len(ranked) // 3)]
    topic_freq: dict[str, int] = defaultdict(int)
    people_freq: dict[str, int] = defaultdict(int)
    for p in top:
        for kw in T.extract_keywords(p.title, limit=6):
            topic_freq[kw] += 1
        for person in T.extract_tagged_people(p.title):
            people_freq[person] += 1
    stats.topics = [w for w, c in sorted(topic_freq.items(), key=lambda kv: (-kv[1], kv[0])) if c >= 2][:8]
    stats.people = [p for p, c in sorted(people_freq.items(), key=lambda kv: (-kv[1], kv[0])) if c >= 2][:8]
    return stats
