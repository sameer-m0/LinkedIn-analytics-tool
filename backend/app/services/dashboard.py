"""Dashboard aggregation service.

Pulls from repositories and shapes data into the response schemas. Keeps all
period/comparison math in ``app.core.dates`` so it stays unit-testable.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date

from sqlalchemy.orm import Session

from app.core.dates import (
    ComparisonMode,
    DateRange,
    RangePreset,
    comparison_range,
    pct_delta,
    resolve_range,
)
from app.models.demographic import DemographicDimension
from app.repositories.demographic_repository import DemographicRepository
from app.repositories.metric_repository import MetricRepository
from app.repositories.post_repository import PostRepository
from app.schemas.dashboard import (
    CategoryValue,
    ContentResponse,
    FollowersResponse,
    KPI,
    OverviewResponse,
    PostRow,
    Series,
    TimePoint,
    TopPost,
    VisitorsResponse,
)

_DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class DashboardService:
    def __init__(self, db: Session) -> None:
        self.metrics = MetricRepository(db)
        self.posts = PostRepository(db)
        self.demographics = DemographicRepository(db)

    # --- range helpers ---
    def resolve(
        self,
        preset: RangePreset,
        today: date,
        custom_start: date | None,
        custom_end: date | None,
    ) -> DateRange:
        return resolve_range(
            preset,
            today=today,
            custom_start=custom_start,
            custom_end=custom_end,
            all_time_floor=self.metrics.earliest_date(),
        )

    def _sum_metric(self, source: str, metric: str, rng: DateRange) -> float | None:
        rows = self.metrics.range(source, metric, rng.start, rng.end)
        if not rows:
            return None
        return sum(r.value for r in rows)

    def _avg_metric(self, source: str, metric: str, rng: DateRange) -> float | None:
        rows = self.metrics.range(source, metric, rng.start, rng.end)
        if not rows:
            return None
        return sum(r.value for r in rows) / len(rows)

    # --- Overview ---
    def overview(self, rng: DateRange, mode: ComparisonMode) -> OverviewResponse:
        prev = comparison_range(rng, mode)
        kpis: list[KPI] = []

        def make_kpi(key, label, cur, previous, spark, unit="count"):
            return KPI(
                key=key, label=label, value=cur, previous=previous,
                delta_pct=pct_delta(cur, previous), sparkline=spark, unit=unit,
            )

        # Net follower growth (prefer total, fall back to organic).
        for follower_metric in ("total_followers", "organic_followers"):
            cur = self._sum_metric("followers", follower_metric, rng)
            if cur is not None:
                prev_v = self._sum_metric("followers", follower_metric, prev) if prev else None
                spark = self._sparkline("followers", follower_metric, rng)
                kpis.append(make_kpi("net_follower_growth", "Net Follower Growth", cur, prev_v, spark))
                break

        imp_cur = self._sum_metric("content", "impressions", rng)
        kpis.append(make_kpi(
            "impressions", "Impressions", imp_cur,
            self._sum_metric("content", "impressions", prev) if prev else None,
            self._sparkline("content", "impressions", rng),
        ))

        er_cur = self._avg_metric("content", "engagement_rate", rng)
        kpis.append(make_kpi(
            "engagement_rate", "Engagement Rate",
            er_cur * 100 if er_cur is not None else None,
            (lambda p: p * 100 if p is not None else None)(
                self._avg_metric("content", "engagement_rate", prev) if prev else None
            ),
            [v * 100 for v in self._sparkline("content", "engagement_rate", rng)],
            unit="percent",
        ))

        uv_cur = self._sum_metric("visitors", "unique_visitors", rng)
        kpis.append(make_kpi(
            "unique_visitors", "Unique Visitors", uv_cur,
            self._sum_metric("visitors", "unique_visitors", prev) if prev else None,
            self._sparkline("visitors", "unique_visitors", rng),
        ))

        return OverviewResponse(
            range_start=rng.start, range_end=rng.end, kpis=kpis, top_post=self._top_post(rng)
        )

    def _sparkline(self, source: str, metric: str, rng: DateRange) -> list[float]:
        rows = self.metrics.range(source, metric, rng.start, rng.end)
        return [r.value for r in rows]

    def _top_post(self, rng: DateRange) -> TopPost | None:
        posts = self.posts.range(rng.start, rng.end)
        if not posts:
            return None
        top = max(posts, key=lambda p: p.impressions)
        return TopPost(
            post_url=top.post_url, title=top.title, post_type=top.post_type,
            impressions=top.impressions, engagement_rate=top.engagement_rate,
        )

    # --- Followers ---
    def followers(self, rng: DateRange) -> FollowersResponse:
        metric = "total_followers" if self.metrics.range("followers", "total_followers", rng.start, rng.end) else "organic_followers"
        rows = self.metrics.range("followers", metric, rng.start, rng.end)
        daily = [TimePoint(date=r.metric_date, value=r.value) for r in rows]

        rolling = []
        window: list[float] = []
        for r in rows:
            window.append(r.value)
            if len(window) > 7:
                window.pop(0)
            rolling.append(TimePoint(date=r.metric_date, value=sum(window) / len(window)))

        cumulative, running = [], 0.0
        for r in rows:
            running += r.value
            cumulative.append(TimePoint(date=r.metric_date, value=running))

        demos: dict[str, list[CategoryValue]] = {}
        for dim in DemographicDimension:
            latest = self.demographics.latest_snapshot_date(dim)
            snaps = self.demographics.by_dimension(dim)
            latest_rows = [s for s in snaps if s.snapshot_date == latest] if latest else []
            latest_rows.sort(key=lambda s: s.value, reverse=True)
            demos[dim.value] = [CategoryValue(category=s.category, value=s.value) for s in latest_rows[:10]]

        return FollowersResponse(
            daily=Series(metric=metric, points=daily),
            rolling_7d=Series(metric=f"{metric}_rolling_7d", points=rolling),
            cumulative=Series(metric=f"{metric}_cumulative", points=cumulative),
            demographics=demos,
        )

    # --- Visitors ---
    def visitors(self, rng: DateRange) -> VisitorsResponse:
        pv = [TimePoint(date=r.metric_date, value=r.value)
              for r in self.metrics.range("visitors", "page_views", rng.start, rng.end)]
        uv = [TimePoint(date=r.metric_date, value=r.value)
              for r in self.metrics.range("visitors", "unique_visitors", rng.start, rng.end)]

        desktop = self._sum_metric("visitors", "desktop_page_views", rng) or 0.0
        mobile = self._sum_metric("visitors", "mobile_page_views", rng) or 0.0
        device = [CategoryValue(category="Desktop", value=desktop), CategoryValue(category="Mobile", value=mobile)]

        # Section views: any visitors metric that is not a top-line/device metric.
        section = [
            CategoryValue(category=m, value=self._sum_metric("visitors", m, rng) or 0.0)
            for m in ("page_views", "unique_visitors")
        ]

        uv_total = self._sum_metric("visitors", "unique_visitors", rng)
        foll_total = self._sum_metric("followers", "total_followers", rng) or self._sum_metric(
            "followers", "organic_followers", rng
        )
        ratio = (foll_total / uv_total) if (uv_total and foll_total) else None

        return VisitorsResponse(
            page_views=Series(metric="page_views", points=pv),
            unique_visitors=Series(metric="unique_visitors", points=uv),
            section_views=section,
            device_split=device,
            followers_per_unique_visitor=ratio,
        )

    # --- Content ---
    def content(self, rng: DateRange) -> ContentResponse:
        imp = [TimePoint(date=r.metric_date, value=r.value)
               for r in self.metrics.range("content", "impressions", rng.start, rng.end)]
        er = [TimePoint(date=r.metric_date, value=r.value * 100)
              for r in self.metrics.range("content", "engagement_rate", rng.start, rng.end)]
        posts = self.posts.range(rng.start, rng.end)

        rows = [
            PostRow(
                date=p.posted_at.date() if p.posted_at else None,
                post_type=p.post_type, impressions=p.impressions, ctr=p.ctr,
                engagement_rate=p.engagement_rate, reactions=p.reactions,
                comments=p.comments, reposts=p.reposts, post_url=p.post_url, title=p.title,
            )
            for p in sorted(posts, key=lambda x: x.impressions, reverse=True)
        ]

        by_type = self._avg_by(posts, key=lambda p: p.post_type or "Unknown", value=lambda p: p.engagement_rate)
        by_dow = self._avg_by(
            posts, key=lambda p: _DOW[p.posted_at.weekday()] if p.posted_at else "Unknown",
            value=lambda p: float(p.impressions),
        )
        by_hour = self._avg_by(
            posts, key=lambda p: _hour_bucket(p.posted_at.hour) if p.posted_at else "Unknown",
            value=lambda p: float(p.impressions),
        )

        return ContentResponse(
            impressions_over_time=Series(metric="impressions", points=imp),
            engagement_over_time=Series(metric="engagement_rate", points=er),
            posts=rows, by_post_type=by_type, by_day_of_week=by_dow, by_hour_bucket=by_hour,
        )

    @staticmethod
    def _avg_by(posts, key, value) -> list[CategoryValue]:
        buckets: dict[str, list[float]] = defaultdict(list)
        for p in posts:
            v = value(p)
            if v is not None:
                buckets[key(p)].append(v)
        return [CategoryValue(category=k, value=sum(vs) / len(vs)) for k, vs in buckets.items()]


def _hour_bucket(hour: int) -> str:
    if hour < 6:
        return "00-06"
    if hour < 12:
        return "06-12"
    if hour < 18:
        return "12-18"
    return "18-24"
