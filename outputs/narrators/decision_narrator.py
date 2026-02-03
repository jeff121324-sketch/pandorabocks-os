from typing import Dict, Any, Optional

from llm_registry import LLMRegistry


CANONICAL_KEYS = [
    "title",
    "summary",
    "decision",
    "confidence",
    "reasons",
    "notes",
]


class DecisionNarrator:
    """
    Uses LLM to narrate a governance decision into a canonical,
    human-readable decision schema.
    """

    def __init__(
        self,
        registry: LLMRegistry,
        strategy: str = "lowest_cost",
    ):
        """
        Args:
            registry: LLMRegistry instance
            strategy: model selection strategy (e.g. lowest_cost, preferred, env_based)
        """
        self.registry = registry
        self.strategy = strategy

    def narrate(
        self,
        decision: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Produce canonical decision schema.

        Audit mode:
            - deterministic
            - no LLM
            - no registry routing
        """

        # 🔑 Audit bypass（重點）
        if decision.get("audit", False):
            return self._render_deterministic(decision, context)

        # -------------------------------
        # Production mode（未來才會用）
        # -------------------------------
        try:
            # 新版介面（strategy-based）
            llm = self.registry.select(self.strategy)
        except TypeError:
            # 舊版介面（name-based）
            llm = self.registry.select()

        prompt = self._build_prompt(decision, context)

        response = llm.generate_json(
            prompt=prompt,
            required_keys=CANONICAL_KEYS,
        )

        return self._normalize(response)

    # ------------------------------------------------------------------

    def _build_prompt(
        self,
        decision: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> str:
        return f"""
You are the internal narrator of an AI governance system.

Your task:
- Explain the system's OWN decision to a human.
- Do NOT mention models, algorithms, or indicators.
- Be calm, professional, and accountable.
- Output JSON only.

Decision input:
{decision}

Context (optional):
{context}

Output MUST be valid JSON with keys:
{CANONICAL_KEYS}
"""

    def _normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure all canonical keys exist.
        """
        return {key: data.get(key) for key in CANONICAL_KEYS}
    
    def _render_deterministic(
        self,
        decision: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Deterministic narration for Audit Runtime.
        Shows REAL persona confidence even if BLOCKED.
        """

        personas = decision.get("personas", {})
        result = decision.get("result")
        reason = decision.get("reason")

        narrated_personas = {}

        for name, p in personas.items():
            if not isinstance(p, dict):
                continue
    
            narrated_personas[name] = {
                "stance": p.get("stance") or p.get("stance_hint"),
                "confidence": p.get("confidence", 0.0),
                "execution": "EXECUTED" if result == "ALLOW" else "BLOCKED",
                "blocked_reason": None if result == "ALLOW" else reason,
           }

        return {
            "title": "Trading Decision Audit Report",
            "summary": f"Decision result: {result}",
            "decision": result,

            # 🔑 總體 confidence 仍保留（系統健康指標）
            "confidence": self._aggregate_confidence(decision),

            "reasons": [reason],

            "notes": {
                "personas": narrated_personas,
                "audit": True,
            },
        }
    def _aggregate_confidence(self, decision: Dict[str, Any]) -> float:
        """
        Deterministic confidence aggregation for Audit Runtime.
        Simple, explainable, replay-safe.
        """
        personas = decision.get("personas", {})
        confidences = []

        for p in personas.values():
            if isinstance(p, dict):
                c = p.get("confidence")
                if isinstance(c, (int, float)):
                    confidences.append(c)

        if not confidences:
            return 0.0

        # Audit 預設策略：取最大信心值（保守、可解釋）
        return round(max(confidences), 3)

