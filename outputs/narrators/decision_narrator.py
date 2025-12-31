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
        Produce canonical decision schema via LLM.
        """
        llm = self.registry.select(strategy=self.strategy)

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
