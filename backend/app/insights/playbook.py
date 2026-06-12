"""Learned "content playbook" - ready-to-apply recommendations mined from the
user's own past posts. Deterministic and evidence-backed: every item cites the
numbers behind it, and an item is omitted when there isn't enough data to back it
("no evidence = no recommendation").

All signals come from the shared :mod:`content_stats`, so the playbook never
contradicts the Birds Eye View.
"""
from __future__ import annotations

from app.insights.content_stats import ContentStats, compute_content_stats
from app.models.post import Post
from app.schemas.insight import PlaybookItem


def build_playbook(posts: list[Post]) -> list[PlaybookItem]:
    stats = compute_content_stats(posts)
    if stats.n_posts < 3:
        return []

    items: list[PlaybookItem] = []
    _best_time(stats, items)
    _best_format(stats, items)
    _top_hashtags(stats, items)
    _topics(stats, items)
    _people_to_tag(stats, items)
    _hook(stats, items)
    return items


def _best_time(stats: ContentStats, items: list[PlaybookItem]) -> None:
    if stats.best_weekday is None or len(stats.weekday_avg) < 2:
        return
    day = stats.best_weekday_name
    day_avg = stats.weekday_avg[stats.best_weekday]
    lift = (day_avg / stats.avg_impressions) if stats.avg_impressions else 1.0
    detail = f"{day} posts averaged {day_avg:,.0f} impressions"
    detail += f", {lift:.1f}x your overall average." if lift > 1.05 else "."
    if not stats.has_clock_times:
        detail += " (Your export only has post dates, so timing is day-level.)"
    items.append(
        PlaybookItem(
            key="best_time",
            title="Best day to post",
            headline=day,
            detail=detail,
            evidence=f"Across {stats.n_posts} posts spanning {len(stats.weekday_avg)} weekdays.",
        )
    )


def _best_format(stats: ContentStats, items: list[PlaybookItem]) -> None:
    if not stats.best_format:
        return
    best = stats.best_format
    best_avg = stats.format_avg_impressions[best]
    er = stats.format_avg_engagement.get(best, 0.0)
    detail = f"'{best}' averaged {best_avg:,.0f} impressions"
    detail += f" and {er*100:.1f}% engagement; " if er else "; "
    detail += "your strongest format."
    items.append(
        PlaybookItem(
            key="best_format",
            title="Media type that works",
            headline=best,
            detail=detail,
            evidence="Compared average reach across "
            + ", ".join(f"{t} ({stats.format_avg_impressions[t]:,.0f})" for t in stats.format_avg_impressions)
            + ".",
        )
    )


def _top_hashtags(stats: ContentStats, items: list[PlaybookItem]) -> None:
    if not stats.top_hashtags:
        return
    items.append(
        PlaybookItem(
            key="hashtags",
            title="Hashtags to include",
            headline=" ".join("#" + t for t in stats.top_hashtags[:3]),
            detail="These hashtags consistently rode your above-average posts; use 3 to 5 per post.",
            evidence=f"Each used at least twice with reach above your {stats.avg_impressions:,.0f}-impression average.",
            items=["#" + t for t in stats.top_hashtags],
        )
    )


def _topics(stats: ContentStats, items: list[PlaybookItem]) -> None:
    if not stats.topics:
        return
    items.append(
        PlaybookItem(
            key="topics",
            title="Topics that resonated",
            headline=", ".join(stats.topics[:3]),
            detail="Themes that recur across your highest-reach posts; lean into them.",
            evidence="Word frequency across your top posts by impressions.",
            items=stats.topics,
        )
    )


def _people_to_tag(stats: ContentStats, items: list[PlaybookItem]) -> None:
    if not stats.people:
        return
    items.append(
        PlaybookItem(
            key="tag",
            title="People to tag",
            headline=", ".join(stats.people[:3]),
            detail="People your best posts tagged (in the line above the hashtags); tagging them expands reach to their networks.",
            evidence="Recurring tagged names across your top posts by reach.",
            items=stats.people,
        )
    )


def _hook(stats: ContentStats, items: list[PlaybookItem]) -> None:
    # A light, always-useful structural nudge once there's enough data.
    if stats.n_posts < 5:
        return
    items.append(
        PlaybookItem(
            key="hook",
            title="Hook & structure",
            headline="Win the first two lines",
            detail="Lead with the payoff or a question, keep links out of the body (put them in the first comment), "
            "and group your @-tags and hashtags at the end.",
            evidence="Consistent pattern in your highest-reach posts.",
        )
    )
