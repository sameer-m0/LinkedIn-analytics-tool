"""Learned "content playbook" — ready-to-apply recommendations mined from the
user's own past posts. Deterministic and evidence-backed: every item cites the
numbers behind it, and an item is omitted when there isn't enough data to back it
("no evidence = no recommendation").
"""
from __future__ import annotations

from collections import defaultdict

from app.insights import text_utils as T
from app.models.post import Post
from app.schemas.insight import PlaybookItem

_DOW = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _hour_bucket(hour: int) -> str:
    if hour < 6:
        return "12–6 AM"
    if hour < 12:
        return "6 AM–12 PM"
    if hour < 18:
        return "12–6 PM"
    return "6 PM–12 AM"


def _avg(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def build_playbook(posts: list[Post]) -> list[PlaybookItem]:
    posts = [p for p in posts if p.impressions is not None]
    items: list[PlaybookItem] = []
    if len(posts) < 3:
        return items

    overall_avg = _avg([p.impressions for p in posts])
    # "High performers" = top third by impressions, used to mine what works.
    ranked = sorted(posts, key=lambda p: p.impressions, reverse=True)
    top = ranked[: max(3, len(ranked) // 3)]

    _best_time(posts, overall_avg, items)
    _best_format(posts, items)
    _top_hashtags(posts, overall_avg, items)
    _topics(top, items)
    _brands_to_tag(top, items)
    _hook_pattern(top, posts, items)
    return items


def _best_time(posts, overall_avg, items) -> None:
    dated = [p for p in posts if p.posted_at]
    if len(dated) < 4:
        return
    by_day: dict[int, list[int]] = defaultdict(list)
    by_bucket: dict[str, list[int]] = defaultdict(list)
    for p in dated:
        by_day[p.posted_at.weekday()].append(p.impressions)
        by_bucket[_hour_bucket(p.posted_at.hour)].append(p.impressions)

    best_day = max(by_day, key=lambda d: _avg(by_day[d]))
    day_avg = _avg(by_day[best_day])
    # Only suggest an hour window if posts actually carry varied hours.
    has_hours = any(p.posted_at.hour != 0 for p in dated)
    best_bucket = max(by_bucket, key=lambda b: _avg(by_bucket[b])) if has_hours else None

    headline = _DOW[best_day] + (f" · {best_bucket}" if best_bucket else "")
    lift = (day_avg / overall_avg) if overall_avg else 1.0
    items.append(
        PlaybookItem(
            key="best_time",
            title="Best time to post",
            headline=headline,
            detail=f"{_DOW[best_day]} posts averaged {day_avg:,.0f} impressions"
            + (f", {lift:.1f}× your overall average." if lift > 1 else "."),
            evidence=f"Based on {len(dated)} dated posts across {len(by_day)} weekdays.",
        )
    )


def _best_format(posts, items) -> None:
    by_type_imp: dict[str, list[int]] = defaultdict(list)
    by_type_er: dict[str, list[float]] = defaultdict(list)
    for p in posts:
        if p.post_type:
            by_type_imp[p.post_type].append(p.impressions)
            if p.engagement_rate is not None:
                by_type_er[p.post_type].append(p.engagement_rate)
    # Need at least two formats to make a comparison meaningful.
    if len(by_type_imp) < 2:
        return
    best = max(by_type_imp, key=lambda t: _avg(by_type_imp[t]))
    best_avg = _avg(by_type_imp[best])
    er = _avg(by_type_er.get(best, []))
    items.append(
        PlaybookItem(
            key="best_format",
            title="Media type that works",
            headline=best,
            detail=f"'{best}' averaged {best_avg:,.0f} impressions"
            + (f" and {er*100:.1f}% engagement" if er else "")
            + " — your strongest format.",
            evidence="Compared average reach across "
            + ", ".join(f"{t} ({len(v)})" for t, v in by_type_imp.items())
            + ".",
        )
    )


def _top_hashtags(posts, overall_avg, items) -> None:
    agg: dict[str, list[int]] = defaultdict(list)
    for p in posts:
        for t in T.extract_hashtags(p.title):
            agg[t].append(p.impressions)
    # Tags used at least twice, ranked by average reach, above overall average.
    ranked = sorted(
        ((t, imps) for t, imps in agg.items() if len(imps) >= 2),
        key=lambda kv: _avg(kv[1]),
        reverse=True,
    )
    winners = [t for t, imps in ranked if _avg(imps) >= overall_avg][:8]
    if not winners:
        return
    items.append(
        PlaybookItem(
            key="hashtags",
            title="Hashtags to include",
            headline=" ".join("#" + t for t in winners[:3]),
            detail="These hashtags consistently rode your above-average posts. Use 3–5 per post.",
            evidence=f"Each used ≥2 times with average reach above your {overall_avg:,.0f}-impression baseline.",
            items=["#" + t for t in winners],
        )
    )


def _topics(top_posts, items) -> None:
    freq: dict[str, int] = defaultdict(int)
    for p in top_posts:
        for kw in T.extract_keywords(p.title, limit=6):
            freq[kw] += 1
    winners = [w for w, c in sorted(freq.items(), key=lambda kv: (-kv[1], kv[0])) if c >= 2][:8]
    if not winners:
        return
    items.append(
        PlaybookItem(
            key="topics",
            title="Topics that resonated",
            headline=", ".join(winners[:3]),
            detail="Themes that recur across your highest-reach posts — lean into them.",
            evidence=f"Word frequency across your top {len(top_posts)} posts by impressions.",
            items=winners,
        )
    )


def _brands_to_tag(top_posts, items) -> None:
    freq: dict[str, int] = defaultdict(int)
    for p in top_posts:
        # @-mentions first (most reliable); fall back to recurring proper nouns.
        for m in T.extract_mentions(p.title):
            freq[m] += 2
        for b in T.extract_brands(p.title):
            freq[b] += 1
    winners = [b for b, c in sorted(freq.items(), key=lambda kv: (-kv[1], kv[0])) if c >= 2][:8]
    if not winners:
        return
    items.append(
        PlaybookItem(
            key="tag",
            title="People / pages to tag",
            headline=", ".join(winners[:3]),
            detail="Brands and entities your top posts referenced — tagging them can expand reach to their networks.",
            evidence=f"Recurring mentions across your top {len(top_posts)} posts.",
            items=winners,
        )
    )


def _hook_pattern(top_posts, all_posts, items) -> None:
    if not top_posts:
        return
    q_top = sum(1 for p in top_posts if T.has_question(p.title)) / len(top_posts)
    link_top = sum(1 for p in top_posts if T.has_link(p.title)) / len(top_posts)
    tips: list[str] = []
    if q_top >= 0.4:
        tips.append("open with a question")
    if link_top <= 0.2:
        tips.append("keep links out of the post body (use the first comment)")
    avg_len = sum(T.char_length(p.title) for p in top_posts) / len(top_posts)
    tips.append(f"aim for ~{int(round(avg_len / 100.0) * 100)} characters")
    if not tips:
        return
    items.append(
        PlaybookItem(
            key="hook",
            title="Hook & structure",
            headline="Write for the first two lines",
            detail="Your best posts tend to " + "; ".join(tips) + ".",
            evidence=f"Patterns shared by your top {len(top_posts)} posts by reach.",
        )
    )
