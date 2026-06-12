"""Learned, always-evidence-backed insights derived from the shared ContentStats.

These widen the recommendation pool (beyond the threshold-gated rules) so the
Insights page has enough genuinely-supported cards to rotate a fresh subset on
each reload. Every one cites real numbers; none is generated without data.
"""
from __future__ import annotations

from app.insights.content_stats import ContentStats, compute_content_stats
from app.models.post import Post
from app.schemas.insight import Insight


def build_learned_insights(posts: list[Post]) -> list[Insight]:
    stats = compute_content_stats(posts)
    if stats.n_posts < 3:
        return []
    out: list[Insight] = []

    # Best day to post.
    if stats.best_weekday is not None and stats.avg_impressions > 0:
        day_avg = stats.weekday_avg[stats.best_weekday]
        lift = day_avg / stats.avg_impressions
        if lift > 1.1:
            out.append(Insight(
                rule_id="learn_best_day",
                title=f"{stats.best_weekday_name} is your strongest day",
                evidence=f"{stats.best_weekday_name} posts average {day_avg:,.0f} impressions, {lift:.1f}x your overall {stats.avg_impressions:,.0f}.",
                impact_score=min(100.0, (lift - 1) * 55),
                confidence_score=0.7,
                recommendation=f"Schedule priority posts for {stats.best_weekday_name}.",
                supporting_metrics={"day_reach": day_avg, "overall_reach": stats.avg_impressions},
            ))

    # Strongest single hashtag.
    if stats.hashtag_stats:
        best = max((s for s in stats.hashtag_stats if s.uses >= 2), key=lambda s: s.avg_impressions, default=None)
        if best and stats.avg_impressions > 0 and best.avg_impressions > stats.avg_impressions * 1.2:
            lift = best.avg_impressions / stats.avg_impressions
            out.append(Insight(
                rule_id="learn_top_hashtag",
                title=f"#{best.tag} consistently over-reaches",
                evidence=f"#{best.tag} averages {best.avg_impressions:,.0f} impressions across {best.uses} posts, {lift:.1f}x your average.",
                impact_score=min(100.0, (lift - 1) * 45),
                confidence_score=min(1.0, best.uses / 5),
                recommendation=f"Keep #{best.tag} in your rotation; pair it with 2 to 4 related tags.",
                supporting_metrics={"hashtag_reach": best.avg_impressions, "uses": best.uses},
            ))

    # Topics that resonate.
    if stats.topics:
        out.append(Insight(
            rule_id="learn_topics",
            title="Lean into your proven topics",
            evidence="Recurring themes in your top posts: " + ", ".join(stats.topics[:5]) + ".",
            impact_score=45.0,
            confidence_score=0.6,
            recommendation=f"Plan your next posts around {', '.join(stats.topics[:3])}.",
            supporting_metrics={"topic_count": float(len(stats.topics))},
        ))

    # People to tag.
    if stats.people:
        out.append(Insight(
            rule_id="learn_tag_people",
            title="Tag the people who amplify you",
            evidence="Your top posts repeatedly tagged: " + ", ".join(stats.people[:5]) + ".",
            impact_score=50.0,
            confidence_score=0.6,
            recommendation=f"When relevant, tag {', '.join(stats.people[:3])}; their networks extend your reach.",
            supporting_metrics={"people_count": float(len(stats.people))},
        ))

    # Best format (only when there are >=2 formats).
    if stats.best_format:
        out.append(Insight(
            rule_id="learn_best_format",
            title=f"{stats.best_format} is your top format",
            evidence=f"'{stats.best_format}' averages {stats.format_avg_impressions[stats.best_format]:,.0f} impressions, your highest format.",
            impact_score=45.0,
            confidence_score=0.6,
            recommendation=f"Produce more {stats.best_format} content.",
            supporting_metrics={"format_reach": stats.format_avg_impressions[stats.best_format]},
        ))

    # Hook / structure nudge.
    out.append(Insight(
        rule_id="learn_hook",
        title="Engineer the first two lines",
        evidence="Across your best posts, the opening line carries the click; links in the body and a wall of text suppress it.",
        impact_score=35.0,
        confidence_score=0.55,
        recommendation="Open with the payoff or a question, move links to the first comment, and group tags and hashtags at the end.",
        supporting_metrics={},
    ))
    return out
