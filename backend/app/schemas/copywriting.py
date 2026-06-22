from __future__ import annotations

from datetime import date
from pydantic import BaseModel


class PostCopywritingAnalysis(BaseModel):
    post_id: int
    post_url: str
    posted_at: date | None
    post_type: str | None
    title: str | None
    impressions: int
    engagement_rate: float | None
    
    # Analysis fields
    hook: str
    hook_effectiveness: str  # "High", "Medium", "Low"
    tone: str
    tone_explanation: str
    key_hooks: list[str] = []
    convincing_elements: list[str] = []
    improvement_suggestions: list[str] = []


class CopywritingListResponse(BaseModel):
    posts: list[PostCopywritingAnalysis]
    total_count: int
