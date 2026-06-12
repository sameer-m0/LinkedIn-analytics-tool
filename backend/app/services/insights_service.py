"""Builds an InsightContext from the repositories and runs the engine."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.dates import ComparisonMode, DateRange, comparison_range
from app.insights.base import InsightContext
from app.insights.engine import InsightsEngine
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

    def generate(self, rng: DateRange, mode: ComparisonMode = ComparisonMode.PREVIOUS_PERIOD) -> list[Insight]:
        return self.engine.run(self._context(rng, mode))

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
