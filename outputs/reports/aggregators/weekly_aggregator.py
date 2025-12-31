# aisop/outputs/reports/aggregators/weekly_aggregator.py

from collections import Counter
from statistics import mean
from typing import Dict, Any

from .base import BaseAggregator


class WeeklyAggregator(BaseAggregator):
    """
    Aggregate governance decisions for a single week.
    """

    def aggregate(self) -> Dict[str, Any]:
        decisions = self.decisions

        decision_dist = Counter(
            d["decision"].get("action")
            for d in decisions
            if isinstance(d.get("decision"), dict)
            and d["decision"].get("action") is not None
        )

        confidences = [
            d["decision"].get("confidence")
            for d in decisions
            if isinstance(d.get("decision"), dict)
            and isinstance(d["decision"].get("confidence"), (int, float))
        ]

        risk_flags = Counter(
            flag
            for d in decisions
            if isinstance(d.get("decision"), dict)
            for flag in d["decision"].get("risk_flags", [])
        )

        return {
            "period": "weekly",
            "total_decisions": len(decisions),
            "decision_distribution": dict(decision_dist),
            "confidence_avg": round(mean(confidences), 4) if confidences else None,
            "risk_summary": dict(risk_flags),
        }