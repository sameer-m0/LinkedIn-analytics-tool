from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class TimePoint(BaseModel):
    date: date
    value: float


class Series(BaseModel):
    metric: str
    points: list[TimePoint]


class KPI(BaseModel):
    key: str
    label: str
    value: float | None
    previous: float | None = None
    delta_pct: float | None = None
    sparkline: list[float] = []
    unit: str = "count"  # count | percent


class TopPost(BaseModel):
    post_url: str
    title: str | None
    post_type: str | None
    impressions: int
    engagement_rate: float | None


class OverviewResponse(BaseModel):
    range_start: date
    range_end: date
    kpis: list[KPI]
    top_post: TopPost | None = None
    top_posts: list[TopPost] = []



class CategoryValue(BaseModel):
    category: str
    value: float


class FollowersResponse(BaseModel):
    daily: Series
    rolling_7d: Series
    cumulative: Series
    demographics: dict[str, list[CategoryValue]]


class VisitorsResponse(BaseModel):
    page_views: Series
    unique_visitors: Series
    section_views: list[CategoryValue]
    device_split: list[CategoryValue]
    followers_per_unique_visitor: float | None


class PostRow(BaseModel):
    date: date | None
    post_type: str | None
    impressions: int
    ctr: float | None
    engagement_rate: float | None
    reactions: int
    comments: int
    reposts: int
    post_url: str
    title: str | None


class ContentResponse(BaseModel):
    impressions_over_time: Series
    engagement_over_time: Series
    posts: list[PostRow]
    by_post_type: list[CategoryValue]
    by_day_of_week: list[CategoryValue]
    by_hour_bucket: list[CategoryValue]
