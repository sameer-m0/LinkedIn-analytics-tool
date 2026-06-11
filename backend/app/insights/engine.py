"""Insights engine: instantiates rules from config and runs them.

Extensible: register a new rule by adding it to ``rules.ALL_RULES`` and a
config entry; the engine discovers it automatically. Results are sorted by
impact * confidence so the most actionable recommendations surface first.
"""
from __future__ import annotations

from app.insights.base import InsightContext, Rule
from app.insights.config import DEFAULT_CONFIG
from app.insights.rules import ALL_RULES
from app.schemas.insight import Insight


class InsightsEngine:
    def __init__(self, config: dict[str, dict[str, float]] | None = None) -> None:
        cfg = config or DEFAULT_CONFIG
        self.rules: list[Rule] = [
            rule_cls(cfg.get(rule_cls.rule_id, {})) for rule_cls in ALL_RULES
        ]

    def run(self, ctx: InsightContext) -> list[Insight]:
        insights: list[Insight] = []
        for rule in self.rules:
            insight = rule.evaluate(ctx)
            if insight is not None and insight.supporting_metrics:  # no evidence => skip
                insights.append(insight)
        insights.sort(key=lambda i: i.impact_score * i.confidence_score, reverse=True)
        return insights
