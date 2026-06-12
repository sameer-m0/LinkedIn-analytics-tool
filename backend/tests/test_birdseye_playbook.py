from datetime import date, datetime

from app.insights.playbook import build_playbook
from app.models.post import Post
from app.services.birdseye_service import BirdsEyeService


def _post(url, impressions, when, *, ptype=None, title="", er=0.05):
    return Post(
        post_url=url, impressions=impressions, posted_at=when, post_type=ptype,
        title=title, engagement_rate=er, ctr=0.01, reactions=0, comments=0,
        reposts=0, clicks=0,
    )


def _analyze(posts):
    # Drive the per-month analyzer directly (no DB needed).
    svc = BirdsEyeService.__new__(BirdsEyeService)
    by_month = {}
    for p in posts:
        by_month.setdefault(f"{p.posted_at.year}-{p.posted_at.month:02d}", []).append(p)
    months = sorted(by_month)
    totals = {m: sum(p.impressions for p in by_month[m]) for m in months}
    out = []
    for i, m in enumerate(months):
        prev = totals[months[i - 1]] if i > 0 else None
        out.append(svc._analyze_month(m, by_month[m], prev))
    return out


def test_birdseye_month_grouping_and_rise():
    posts = [
        _post("a", 1000, datetime(2026, 1, 5), title="gaming #gaming"),
        _post("b", 500, datetime(2026, 1, 20), title="startups #startups"),
        _post("c", 4000, datetime(2026, 2, 10), title="big news #gaming #forbes"),
        _post("d", 2000, datetime(2026, 2, 15), title="more #gaming"),
    ]
    months = _analyze(posts)
    jan = next(m for m in months if m.month == "2026-01")
    feb = next(m for m in months if m.month == "2026-02")
    assert jan.posts == 2 and jan.total_impressions == 1500
    assert feb.impressions_change_pct is not None and feb.impressions_change_pct > 0
    assert "rose" in feb.trend_narrative.lower()
    assert feb.top_posts[0].impressions == 4000
    assert feb.top_posts[0].factors  # has boom factors


def test_birdseye_low_post_flags_external_link():
    posts = [
        _post("hi", 5000, datetime(2026, 3, 1), title="winner #gaming"),
        _post("mid", 1200, datetime(2026, 3, 2), title="ok #gaming"),
        _post("lo", 100, datetime(2026, 3, 3), title="read https://lnkd.in/x more text"),
    ]
    months = _analyze(posts)
    mar = months[0]
    low_factors = " ".join(f for p in mar.low_posts for f in p.factors).lower()
    assert "link" in low_factors


def test_playbook_learns_time_hashtags_topics():
    posts = []
    # Mondays reach far more; #gaming rides the winners; topic "gaming" recurs.
    for i in range(4):
        posts.append(_post(f"mon{i}", 5000, datetime(2026, 1, 5 + 7 * i), title="gaming studios india #gaming #india"))
    for i in range(4):
        posts.append(_post(f"tue{i}", 500, datetime(2026, 1, 6 + 7 * i), title="random note #misc"))
    pb = {item.key: item for item in build_playbook(posts)}
    assert "best_time" in pb and "Monday" in pb["best_time"].headline
    assert "hashtags" in pb and any("#gaming" in c for c in pb["hashtags"].items)
    assert "topics" in pb and "gaming" in pb["topics"].items


def test_playbook_empty_when_too_few_posts():
    assert build_playbook([_post("a", 100, datetime(2026, 1, 1))]) == []
