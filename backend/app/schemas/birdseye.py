from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class HashtagStat(BaseModel):
    tag: str
    uses: int
    avg_impressions: float


class AnalyzedPost(BaseModel):
    post_url: str
    hook: str
    post_type: str | None
    posted_at: date | None
    impressions: int
    engagement_rate: float | None
    reach_multiple: float | None  # vs the month's median post
    hashtags: list[str] = []
    factors: list[str] = []  # boom drivers (top) or mistakes (low)


class MonthAnalysis(BaseModel):
    month: str  # "2026-03"
    label: str  # "March 2026"
    posts: int
    total_impressions: float
    avg_impressions: float
    median_impressions: float
    prev_month_impressions: float | None = None
    impressions_change_pct: float | None = None
    trend_narrative: str
    top_posts: list[AnalyzedPost] = []
    low_posts: list[AnalyzedPost] = []
    trending_hashtags: list[HashtagStat] = []


class BirdsEyeResponse(BaseModel):
    months: list[MonthAnalysis] = []  # newest first
