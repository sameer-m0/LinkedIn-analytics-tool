from datetime import date, datetime

from app.insights.base import InsightContext
from app.insights.engine import InsightsEngine
from app.models.daily_metric import DailyMetric
from app.models.post import Post


def _post(url, ptype, impressions, er, when, ctr=0.02):
    return Post(
        post_url=url, post_type=ptype, impressions=impressions, engagement_rate=er,
        ctr=ctr, reactions=0, comments=0, reposts=0, clicks=0, posted_at=when,
    )


def test_rule1_post_type_fires():
    posts = [_post(f"u{i}", "video", 1000, 0.10, datetime(2024, 3, 1)) for i in range(5)]
    posts += [_post(f"x{i}", "text", 1000, 0.02, datetime(2024, 3, 2)) for i in range(5)]
    ctx = InsightContext(date(2024, 3, 1), date(2024, 3, 31), posts, [], [])
    insights = InsightsEngine().run(ctx)
    assert any(i.rule_id == "rule_1_post_type" and "video" in i.recommendation for i in insights)


def test_rule1_requires_min_n():
    # Only 2 video posts -> below min_n=5, must not fire.
    posts = [_post(f"u{i}", "video", 1000, 0.20, datetime(2024, 3, 1)) for i in range(2)]
    posts += [_post(f"x{i}", "text", 1000, 0.02, datetime(2024, 3, 2)) for i in range(5)]
    ctx = InsightContext(date(2024, 3, 1), date(2024, 3, 31), posts, [], [])
    assert not any(i.rule_id == "rule_1_post_type" for i in InsightsEngine().run(ctx))


def test_rule3_cadence_drop():
    cur_posts = [_post(f"c{i}", "text", 100, 0.02, datetime(2024, 3, i + 1)) for i in range(2)]
    prev_posts = [_post(f"p{i}", "text", 100, 0.02, datetime(2024, 2, i + 1)) for i in range(8)]
    metrics = [DailyMetric(metric_date=date(2024, 3, 1), source="content", metric="impressions", value=500.0)]
    prev_metrics = [DailyMetric(metric_date=date(2024, 2, 1), source="content", metric="impressions", value=2000.0)]
    ctx = InsightContext(
        date(2024, 3, 1), date(2024, 3, 31), cur_posts, metrics, [],
        prev_posts=prev_posts, prev_metrics=prev_metrics,
    )
    assert any(i.rule_id == "rule_3_cadence" for i in InsightsEngine().run(ctx))


def test_rule6_high_impressions_low_ctr():
    posts = [_post(f"u{i}", "text", 50000, 0.03, datetime(2024, 3, 1), ctr=0.001) for i in range(6)]
    ctx = InsightContext(date(2024, 3, 1), date(2024, 3, 31), posts, [], [])
    assert any(i.rule_id == "rule_6_ctr" for i in InsightsEngine().run(ctx))


def test_no_evidence_no_recommendation():
    # Empty context -> zero insights (the core "no evidence" guarantee).
    ctx = InsightContext(date(2024, 3, 1), date(2024, 3, 31), [], [], [])
    assert InsightsEngine().run(ctx) == []


def test_rule7_post_length_fires():
    posts = [_post(f"c{i}", "text", 1000, 0.10, datetime(2024, 3, 1)) for i in range(3)]
    for p in posts:
        p.title = "Short title"
    long_posts = [_post(f"l{i}", "text", 1000, 0.02, datetime(2024, 3, 2)) for i in range(3)]
    for p in long_posts:
        p.title = "Very long title " * 100
    posts.extend(long_posts)

    ctx = InsightContext(date(2024, 3, 1), date(2024, 3, 31), posts, [], [])
    insights = InsightsEngine().run(ctx)
    assert any(i.rule_id == "rule_7_post_length" for i in insights)


def test_rule8_post_links_fires():
    posts = [_post(f"nl{i}", "text", 1000, 0.10, datetime(2024, 3, 1)) for i in range(3)]
    for p in posts:
        p.title = "Nice title without link"
    link_posts = [_post(f"wl{i}", "text", 1000, 0.02, datetime(2024, 3, 2)) for i in range(3)]
    for p in link_posts:
        p.title = "Title with link https://lnkd.in/test"
    posts.extend(link_posts)

    ctx = InsightContext(date(2024, 3, 1), date(2024, 3, 31), posts, [], [])
    insights = InsightsEngine().run(ctx)
    assert any(i.rule_id == "rule_8_post_links" for i in insights)

