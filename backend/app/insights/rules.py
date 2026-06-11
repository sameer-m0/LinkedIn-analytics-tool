"""The six initial insight rules. Each is deterministic and evidence-backed."""
from __future__ import annotations

from collections import defaultdict

from app.insights.base import InsightContext, Rule
from app.schemas.insight import Insight


def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


class PostTypeEngagementRule(Rule):
    rule_id = "rule_1_post_type"
    title = "A post format is outperforming"

    def evaluate(self, ctx: InsightContext) -> Insight | None:
        min_ratio = self.config["min_ratio"]
        min_n = int(self.config["min_n"])
        by_type: dict[str, list[float]] = defaultdict(list)
        for p in ctx.posts:
            if p.engagement_rate is not None and p.post_type:
                by_type[p.post_type].append(p.engagement_rate)
        if not by_type:
            return None
        overall = _avg([er for ers in by_type.values() for er in ers])
        if overall <= 0:
            return None

        best_type, best_avg, best_n = None, 0.0, 0
        for ptype, ers in by_type.items():
            if len(ers) >= min_n and _avg(ers) >= best_avg:
                best_type, best_avg, best_n = ptype, _avg(ers), len(ers)
        if best_type is None or best_avg < overall * min_ratio:
            return None

        ratio = best_avg / overall
        return Insight(
            rule_id=self.rule_id, title=self.title,
            evidence=(
                f"'{best_type}' posts (n={best_n}) average {best_avg*100:.1f}% engagement vs "
                f"{overall*100:.1f}% overall — {ratio:.1f}x the average."
            ),
            impact_score=self._clamp((ratio - 1) * 40),
            confidence_score=min(1.0, best_n / (min_n * 2)),
            recommendation=f"Publish more '{best_type}' posts; it is your highest-engagement format.",
            supporting_metrics={"format_engagement": best_avg, "overall_engagement": overall, "n": best_n},
        )


class DayOfWeekImpressionsRule(Rule):
    rule_id = "rule_2_day_of_week"
    title = "A weekday drives more impressions"
    _DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    def evaluate(self, ctx: InsightContext) -> Insight | None:
        min_ratio = self.config["min_ratio"]
        min_n = int(self.config["min_n"])
        by_day: dict[int, list[float]] = defaultdict(list)
        for p in ctx.posts:
            if p.posted_at:
                by_day[p.posted_at.weekday()].append(float(p.impressions))
        if not by_day:
            return None
        overall = _avg([v for vs in by_day.values() for v in vs])
        if overall <= 0:
            return None

        best_day, best_avg, best_n = None, 0.0, 0
        for day, vals in by_day.items():
            if len(vals) >= min_n and _avg(vals) >= best_avg:
                best_day, best_avg, best_n = day, _avg(vals), len(vals)
        if best_day is None or best_avg < overall * min_ratio:
            return None

        ratio = best_avg / overall
        name = self._DOW[best_day]
        return Insight(
            rule_id=self.rule_id, title=self.title,
            evidence=(
                f"Posts on {name} (n={best_n}) average {best_avg:,.0f} impressions vs "
                f"{overall:,.0f} overall — {ratio:.1f}x."
            ),
            impact_score=self._clamp((ratio - 1) * 50),
            confidence_score=min(1.0, best_n / (min_n * 2)),
            recommendation=f"Schedule more posts on {name}; it reaches the widest audience.",
            supporting_metrics={"day_impressions": best_avg, "overall_impressions": overall, "n": best_n},
        )


class PostingCadenceRule(Rule):
    rule_id = "rule_3_cadence"
    title = "Posting cadence dropped while reach declined"

    def evaluate(self, ctx: InsightContext) -> Insight | None:
        drop = self.config["freq_drop"]
        cur_n, prev_n = len(ctx.posts), len(ctx.prev_posts)
        if prev_n == 0:
            return None
        freq_change = (cur_n - prev_n) / prev_n
        imp_cur = ctx.metric_sum("content", "impressions")
        imp_prev = ctx.metric_sum("content", "impressions", previous=True)
        if freq_change > -drop or imp_prev <= 0 or imp_cur >= imp_prev:
            return None

        imp_change = (imp_cur - imp_prev) / imp_prev
        return Insight(
            rule_id=self.rule_id, title=self.title,
            evidence=(
                f"Posts fell from {prev_n} to {cur_n} ({freq_change*100:.0f}%) and impressions "
                f"declined {imp_change*100:.0f}% ({imp_prev:,.0f} → {imp_cur:,.0f})."
            ),
            impact_score=self._clamp(abs(imp_change) * 100),
            confidence_score=min(1.0, prev_n / 8),
            recommendation="Restore your previous posting cadence to recover reach.",
            supporting_metrics={"posts_now": cur_n, "posts_prev": prev_n, "impressions_now": imp_cur, "impressions_prev": imp_prev},
        )


class ConversionRule(Rule):
    rule_id = "rule_4_conversion"
    title = "Visitor traffic is up but followers are flat"

    def evaluate(self, ctx: InsightContext) -> Insight | None:
        vis_cur = ctx.metric_sum("visitors", "unique_visitors")
        vis_prev = ctx.metric_sum("visitors", "unique_visitors", previous=True)
        foll_cur = ctx.metric_sum("followers", "total_followers") or ctx.metric_sum("followers", "organic_followers")
        foll_prev = (
            ctx.metric_sum("followers", "total_followers", previous=True)
            or ctx.metric_sum("followers", "organic_followers", previous=True)
        )
        if vis_prev <= 0 or foll_prev <= 0:
            return None
        vis_growth = (vis_cur - vis_prev) / vis_prev
        foll_growth = (foll_cur - foll_prev) / foll_prev
        if vis_growth < self.config["visitor_growth_min"] or abs(foll_growth) > self.config["follower_flat_max"]:
            return None

        return Insight(
            rule_id=self.rule_id, title=self.title,
            evidence=(
                f"Unique visitors grew {vis_growth*100:.0f}% while follower growth was flat "
                f"({foll_growth*100:+.1f}%)."
            ),
            impact_score=self._clamp(vis_growth * 60),
            confidence_score=0.7,
            recommendation="Strengthen page conversion: clearer value proposition, a pinned post, and a follow CTA.",
            supporting_metrics={"visitor_growth": vis_growth, "follower_growth": foll_growth},
        )


class DemographicGrowthRule(Rule):
    rule_id = "rule_5_demographic"
    title = "A demographic segment is growing fast"

    def evaluate(self, ctx: InsightContext) -> Insight | None:
        multiple = self.config["growth_multiple"]
        min_base = self.config["min_base"]
        # Compare each segment's latest two snapshots within the same dimension.
        by_dim_cat: dict[tuple, list] = defaultdict(list)
        for s in ctx.demographics:
            by_dim_cat[(s.dimension, s.category)].append(s)
        growths: list[tuple[str, str, float]] = []
        for (dim, cat), snaps in by_dim_cat.items():
            snaps.sort(key=lambda s: s.snapshot_date)
            if len(snaps) < 2 or snaps[0].value < min_base:
                continue
            g = (snaps[-1].value - snaps[0].value) / snaps[0].value
            growths.append((dim.value, cat, g))
        if len(growths) < 2:
            return None
        growths.sort(key=lambda x: x[2], reverse=True)
        top = growths[0]
        median = sorted(g for _, _, g in growths)[len(growths) // 2]
        if median <= 0 or top[2] < median * multiple:
            return None

        return Insight(
            rule_id=self.rule_id, title=self.title,
            evidence=(
                f"'{top[1]}' ({top[0]}) grew {top[2]*100:.0f}%, over {top[2]/max(median,1e-9):.1f}x "
                f"the median segment ({median*100:.0f}%)."
            ),
            impact_score=self._clamp(top[2] * 50),
            confidence_score=0.6,
            recommendation=f"Create content targeted at '{top[1]}' to compound this momentum.",
            supporting_metrics={"segment_growth": top[2], "median_growth": median},
        )


class HighImpressionsLowCtrRule(Rule):
    rule_id = "rule_6_ctr"
    title = "High-reach posts have weak click-through"

    def evaluate(self, ctx: InsightContext) -> Insight | None:
        low_ctr = self.config["low_ctr"]
        pct = self.config["impression_percentile"]
        posts = [p for p in ctx.posts if p.impressions > 0 and p.ctr is not None]
        if len(posts) < 4:
            return None
        sorted_imp = sorted(p.impressions for p in posts)
        threshold = sorted_imp[int(len(sorted_imp) * pct)]
        high = [p for p in posts if p.impressions >= threshold]
        if not high:
            return None
        avg_ctr = _avg([p.ctr for p in high])
        if avg_ctr >= low_ctr:
            return None

        return Insight(
            rule_id=self.rule_id, title=self.title,
            evidence=(
                f"Your top {len(high)} highest-reach posts (≥{threshold:,.0f} impressions) average "
                f"a {avg_ctr*100:.2f}% CTR — below the {low_ctr*100:.2f}% benchmark."
            ),
            impact_score=self._clamp((low_ctr - avg_ctr) / low_ctr * 60),
            confidence_score=min(1.0, len(high) / 6),
            recommendation="Rework headlines and opening hooks on high-reach posts to convert views into clicks.",
            supporting_metrics={"high_reach_ctr": avg_ctr, "ctr_benchmark": low_ctr, "n": len(high)},
        )


class PostLengthEngagementRule(Rule):
    rule_id = "rule_7_post_length"
    title = "Concise posts drive higher engagement"

    def evaluate(self, ctx: InsightContext) -> Insight | None:
        max_chars = self.config["max_chars"]
        min_ratio = self.config["min_ratio"]
        min_n = int(self.config["min_n"])

        concise_ers = []
        long_ers = []
        for p in ctx.posts:
            if p.engagement_rate is not None and p.title:
                char_len = len(p.title)
                if char_len < max_chars:
                    concise_ers.append(p.engagement_rate)
                else:
                    long_ers.append(p.engagement_rate)

        concise_n = len(concise_ers)
        long_n = len(long_ers)

        if concise_n < min_n or long_n < min_n:
            return None

        concise_avg = _avg(concise_ers)
        long_avg = _avg(long_ers)

        if long_avg <= 0 or concise_avg < long_avg * min_ratio:
            return None

        ratio = concise_avg / long_avg
        return Insight(
            rule_id=self.rule_id,
            title=self.title,
            evidence=(
                f"Concise posts (under {max_chars:,.0f} chars, n={concise_n}) average {concise_avg*100:.1f}% engagement vs "
                f"{long_avg*100:.1f}% for longer posts (n={long_n}) — {ratio:.1f}x higher."
            ),
            impact_score=self._clamp((ratio - 1) * 30),
            confidence_score=min(1.0, (concise_n + long_n) / (min_n * 4)),
            recommendation=f"Keep your posts concise (under {max_chars:,.0f} characters) to optimize for reader engagement and higher engagement rates.",
            supporting_metrics={"concise_avg_er": concise_avg, "long_avg_er": long_avg, "concise_n": concise_n, "long_n": long_n},
        )


class PostLinksEngagementRule(Rule):
    rule_id = "rule_8_post_links"
    title = "Posts without links generate higher engagement"

    def evaluate(self, ctx: InsightContext) -> Insight | None:
        min_ratio = self.config["min_ratio"]
        min_n = int(self.config["min_n"])

        no_links_ers = []
        with_links_ers = []
        for p in ctx.posts:
            if p.engagement_rate is not None and p.title:
                has_link = "http" in p.title or "lnkd.in" in p.title
                if has_link:
                    with_links_ers.append(p.engagement_rate)
                else:
                    no_links_ers.append(p.engagement_rate)

        no_links_n = len(no_links_ers)
        with_links_n = len(with_links_ers)

        if no_links_n < min_n or with_links_n < min_n:
            return None

        no_links_avg = _avg(no_links_ers)
        with_links_avg = _avg(with_links_ers)

        if with_links_avg <= 0 or no_links_avg < with_links_avg * min_ratio:
            return None

        ratio = no_links_avg / with_links_avg
        return Insight(
            rule_id=self.rule_id,
            title=self.title,
            evidence=(
                f"Posts without links (n={no_links_n}) average {no_links_avg*100:.1f}% engagement vs "
                f"{with_links_avg*100:.1f}% for posts with links (n={with_links_n}) — {ratio:.1f}x higher."
            ),
            impact_score=self._clamp((ratio - 1) * 30),
            confidence_score=min(1.0, (no_links_n + with_links_n) / (min_n * 4)),
            recommendation="Avoid placing links in the post copy. Share links in the comments or bio to prevent the LinkedIn algorithm and user behavior from lowering engagement.",
            supporting_metrics={"no_links_avg_er": no_links_avg, "with_links_avg_er": with_links_avg, "no_links_n": no_links_n, "with_links_n": with_links_n},
        )


ALL_RULES: list[type[Rule]] = [
    PostTypeEngagementRule,
    DayOfWeekImpressionsRule,
    PostingCadenceRule,
    ConversionRule,
    DemographicGrowthRule,
    HighImpressionsLowCtrRule,
    PostLengthEngagementRule,
    PostLinksEngagementRule,
]

