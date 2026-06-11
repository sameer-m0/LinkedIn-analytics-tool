"""Rule framework: context, rule contract, and the produced ``Insight``.

A rule is deterministic and pure: given an ``InsightContext`` and config, it
returns an ``Insight`` or ``None``. "No evidence = no recommendation" is
enforced structurally — a rule that cannot cite supporting metrics returns
``None``.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date

from app.models.daily_metric import DailyMetric
from app.models.demographic import DemographicSnapshot
from app.models.post import Post
from app.schemas.insight import Insight


@dataclass
class InsightContext:
    """All data a rule may inspect for the current and comparison windows."""

    range_start: date
    range_end: date
    posts: list[Post]
    metrics: list[DailyMetric]
    demographics: list[DemographicSnapshot]
    prev_posts: list[Post] = field(default_factory=list)
    prev_metrics: list[DailyMetric] = field(default_factory=list)

    def metric_sum(self, source: str, metric: str, *, previous: bool = False) -> float:
        rows = self.prev_metrics if previous else self.metrics
        return sum(r.value for r in rows if r.source == source and r.metric == metric)


class Rule(ABC):
    rule_id: str
    title: str

    def __init__(self, config: dict[str, float]) -> None:
        self.config = config

    @abstractmethod
    def evaluate(self, ctx: InsightContext) -> Insight | None:
        """Return an Insight if the rule fires with evidence, else None."""

    @staticmethod
    def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
        return max(lo, min(hi, value))
