"""Builds an InsightContext from the repositories and runs the engine."""
from __future__ import annotations

import random

from sqlalchemy.orm import Session

from app.core.dates import ComparisonMode, DateRange, comparison_range
from app.insights.base import InsightContext
from app.insights.engine import InsightsEngine
from app.insights.learned import build_learned_insights
from app.insights.playbook import build_playbook
from app.models.demographic import DemographicDimension
from app.repositories.demographic_repository import DemographicRepository
from app.repositories.metric_repository import MetricRepository
from app.repositories.post_repository import PostRepository
from app.schemas.insight import Insight, PlaybookItem


class InsightsService:
    def __init__(self, db: Session) -> None:
        self.metrics = MetricRepository(db)
        self.posts = PostRepository(db)
        self.demographics = DemographicRepository(db)
        self.engine = InsightsEngine()

    # How many recommendations to surface at once. When more than this qualify,
    # we rotate which subset shows so the page feels fresh on each reload.
    SHOWN = 5

    def generate(self, rng: DateRange, mode: ComparisonMode = ComparisonMode.PREVIOUS_PERIOD) -> list[Insight]:
        ctx = self._context(rng, mode)
        # Pool = threshold-gated rules + always-evidence-backed learned insights.
        pool = self.engine.run(ctx) + build_learned_insights(ctx.posts)
        seen: set[str] = set()
        unique = [i for i in pool if not (i.rule_id in seen or seen.add(i.rule_id))]

        if len(unique) <= self.SHOWN:
            unique.sort(key=lambda i: i.impact_score * i.confidence_score, reverse=True)
            return unique
        chosen = _weighted_sample(unique, self.SHOWN, random.Random())
        chosen.sort(key=lambda i: i.impact_score * i.confidence_score, reverse=True)
        return chosen

    def playbook(self, rng: DateRange) -> list[PlaybookItem]:
        return build_playbook(self.posts.range(rng.start, rng.end))

    def _context(self, rng: DateRange, mode: ComparisonMode) -> InsightContext:
        prev = comparison_range(rng, mode)
        demos = []
        for dim in DemographicDimension:
            demos.extend(self.demographics.by_dimension(dim))

        return InsightContext(
            range_start=rng.start,
            range_end=rng.end,
            posts=self.posts.range(rng.start, rng.end),
            metrics=self.metrics.range(None, None, rng.start, rng.end),
            demographics=demos,
            prev_posts=self.posts.range(prev.start, prev.end) if prev else [],
            prev_metrics=self.metrics.range(None, None, prev.start, prev.end) if prev else [],
        )


def _weighted_sample(insights: list[Insight], k: int, rng: random.Random) -> list[Insight]:
    """Sample ``k`` insights without replacement, weighting higher impact x
    confidence more heavily. Higher-value insights surface more often, but the
    rotation keeps the set varied across reloads."""
    pool = list(insights)
    weights = [i.impact_score * i.confidence_score + 1.0 for i in pool]
    chosen: list[Insight] = []
    for _ in range(min(k, len(pool))):
        total = sum(weights)
        r = rng.random() * total
        acc = 0.0
        idx = 0
        for idx, w in enumerate(weights):
            acc += w
            if r <= acc:
                break
        chosen.append(pool.pop(idx))
        weights.pop(idx)
    return chosen
