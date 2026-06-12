from __future__ import annotations

from pydantic import BaseModel


class Insight(BaseModel):
    rule_id: str
    title: str
    evidence: str
    impact_score: float  # 0..100
    confidence_score: float  # 0..1
    recommendation: str
    supporting_metrics: dict[str, float] = {}


class PlaybookItem(BaseModel):
    """A learned, ready-to-apply recommendation derived from past posts."""

    key: str
    title: str
    headline: str  # the short answer, e.g. "Tuesday, 12–6 PM"
    detail: str
    evidence: str
    items: list[str] = []  # chips: hashtags, brands, topics, etc.


class InsightsResponse(BaseModel):
    range_start: str
    range_end: str
    playbook: list[PlaybookItem] = []
    insights: list[Insight]
