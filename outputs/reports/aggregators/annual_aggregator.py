from collections import Counter
from statistics import mean
from typing import Dict, Any

from .base import BaseAggregator


class AnnualAggregator(BaseAggregator):
    """
    Aggregate governance decisions for a year.

    Focus:
    - Governance effectiveness
    - Long-term risk profile
    - Learning signal presence
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

        governance_entropy = len(action_dist)

        return {
            "period": "annual",
            "total_decisions": len(decisions),
            "governance_entropy": governance_entropy,
            "decision_distribution": dict(action_dist),
            "confidence_avg": round(mean(confidences), 4) if confidences else None,
            "risk_summary": dict(risk_flags),
        }
