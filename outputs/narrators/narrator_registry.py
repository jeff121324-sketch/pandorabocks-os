# aisop/outputs/narrators/narrator_registry.py

from typing import Dict, Any, Protocol


class Narrator(Protocol):
    """
    Every narrator must implement narrate()
    """

    def narrate(self, decision: Dict[str, Any]) -> str:
        ...


class NarratorRegistry:
    """
    Cost / capability aware narrator selector
    """

    def __init__(self):
        self._registry: Dict[str, Narrator] = {}

    def register(self, name: str, narrator: Narrator):
        self._registry[name] = narrator

    def select(
        self,
        *,
        report_type: str,
        env: str = "prod",
        max_cost: str = "low",
    ) -> Narrator:
        """
        Select narrator based on report type and cost policy
        """

        # === 最簡單、但可演進的策略 ===
        if report_type in ("weekly", "monthly"):
            key = "gpt_high"
        elif env == "test":
            key = "stub"
        else:
            key = "gpt_low"

        if key not in self._registry:
            raise RuntimeError(f"No narrator registered for key: {key}")

        return self._registry[key]
