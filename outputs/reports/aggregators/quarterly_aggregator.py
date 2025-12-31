from collections import Counter
from statistics import mean
from typing import Dict, Any

from .base import BaseAggregator


class QuarterlyAggregator(BaseAggregator):
    """
    Aggregate governance decisions for a quarter.

    Focus:
    - Trend direction consistency
    - Dominant decision action
    - Risk accumulation
    """

    def aggregate(self) -> Dict[str, Any]:
        decisions = self.decisions

        actions = [
            d["decision"].get("action")
            for d in decisions
            if isinstance(d.get("decision"), dict)
            and d["decision"].get("action") is not None
        ]

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

        action_dist = Counter(actions)

        dominant_action = (
            action_dist.most_common(1)[0][0]
            if action_dist
            else None
        )

        return {
            "period": "quarterly",
            "total_decisions": len(decisions),
            "dominant_action": dominant_action,
            "decision_distribution": dict(action_dist),
            "confidence_avg": round(mean(confidences), 4) if confidences else None,
            "risk_summary": dict(risk_flags),
        }
