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


class InsightsResponse(BaseModel):
    range_start: str
    range_end: str
    insights: list[Insight]
