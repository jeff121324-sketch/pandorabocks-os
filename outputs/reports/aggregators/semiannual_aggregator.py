from collections import Counter
from statistics import mean
from typing import Dict, Any

from .base import BaseAggregator


class SemiannualAggregator(BaseAggregator):
    """
    Aggregate governance decisions for half a year.

    Focus:
    - Strategy stability
    - Risk correction vs accumulation
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

        strategy_shift = len(action_dist) > 1

        return {
            "period": "semiannual",
            "total_decisions": len(decisions),
            "strategy_shift_detected": strategy_shift,
            "decision_distribution": dict(action_dist),
            "confidence_avg": round(mean(confidences), 4) if confidences else None,
            "risk_summary": dict(risk_flags),
        }
