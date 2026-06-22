from __future__ import annotations

import statistics
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import RangeParams, get_db
from app.repositories.post_repository import PostRepository
from app.insights.copywriting_analyst import analyze_post_copywriting
from app.schemas.copywriting import CopywritingListResponse, PostCopywritingAnalysis

router = APIRouter(prefix="/copywriting", tags=["copywriting"])


@router.get("/posts", response_model=CopywritingListResponse)
def get_analyzed_posts(
    params: Annotated[RangeParams, Depends()],
    db: Annotated[Session, Depends(get_db)],
    search: str | None = None,
    performance_tier: str | None = None,  # "top", "mid", "low"
    tone: str | None = None,  # "Storytelling", "Educational", "Promotional", "Conversational", "Technical", "Insightful"
    sort_by: str = "date",  # "date", "impressions", "engagement_rate"
    sort_order: str = "desc",  # "desc", "asc"
) -> CopywritingListResponse:
    # 1. Fetch posts in the date range
    posts = PostRepository(db).range(params.range.start, params.range.end)
    
    # 2. Fetch all posts to get global benchmarks (median impressions & avg engagement)
    all_posts = PostRepository(db).all()
    if all_posts:
        impressions = [p.impressions for p in all_posts]
        median_impressions = float(statistics.median(impressions)) if impressions else 0.0
        
        total_er = 0.0
        er_count = 0
        for p in all_posts:
            if p.engagement_rate is not None:
                total_er += p.engagement_rate
                er_count += 1
        avg_engagement = total_er / er_count if er_count > 0 else 0.0
    else:
        median_impressions = 0.0
        avg_engagement = 0.0

    # 3. Determine performance tier boundaries for the posts in current range
    # Sort descending by impressions
    posts_sorted_by_reach = sorted(posts, key=lambda x: x.impressions, reverse=True)
    n = len(posts_sorted_by_reach)
    top_boundary = max(1, n // 4) if n >= 4 else 1
    low_boundary = n - top_boundary if n >= 4 else n
    
    top_urls = {p.post_url for p in posts_sorted_by_reach[:top_boundary]} if n > 0 else set()
    low_urls = {p.post_url for p in posts_sorted_by_reach[low_boundary:]} if n >= 4 else set()

    # 4. Analyze all posts in the active range
    analyzed_posts = []
    for p in posts:
        analysis = analyze_post_copywriting(p, median_impressions, avg_engagement)
        
        posted_date = p.posted_at.date() if p.posted_at else None
        
        analyzed_posts.append(
            PostCopywritingAnalysis(
                post_id=p.id,
                post_url=p.post_url,
                posted_at=posted_date,
                post_type=p.post_type,
                title=p.title,
                impressions=p.impressions,
                engagement_rate=p.engagement_rate,
                hook=analysis["hook"],
                hook_effectiveness=analysis["hook_effectiveness"],
                tone=analysis["tone"],
                tone_explanation=analysis["tone_explanation"],
                key_hooks=analysis["key_hooks"],
                convincing_elements=analysis["convincing_elements"],
                improvement_suggestions=analysis["improvement_suggestions"],
            )
        )

    # 5. Filter by Search Query
    if search:
        search_lower = search.lower()
        analyzed_posts = [
            p for p in analyzed_posts
            if p.title and search_lower in p.title.lower()
        ]

    # 6. Filter by Tone
    if tone:
        analyzed_posts = [p for p in analyzed_posts if p.tone == tone]

    # 7. Filter by Performance Tier
    if performance_tier:
        analyzed_posts = [
            p for p in analyzed_posts
            if (performance_tier == "top" and p.post_url in top_urls) or
               (performance_tier == "low" and p.post_url in low_urls) or
               (performance_tier == "mid" and p.post_url not in top_urls and p.post_url not in low_urls)
        ]

    # 8. Sort posts
    def get_sort_key(item: PostCopywritingAnalysis):
        if sort_by == "impressions":
            return item.impressions
        elif sort_by == "engagement_rate":
            return item.engagement_rate or 0.0
        else:
            # date sorting
            return item.posted_at or date.min

    is_reverse = (sort_order == "desc")
    analyzed_posts.sort(key=get_sort_key, reverse=is_reverse)

    return CopywritingListResponse(
        posts=analyzed_posts,
        total_count=len(analyzed_posts)
    )
