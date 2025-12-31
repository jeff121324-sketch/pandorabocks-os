from typing import Dict, Any
from outputs.narrators.decision_narrator import DecisionNarrator


class NarratedOutputDispatcher:
    """
    Adapter that ensures all outputs are self-narrated by the model
    before being dispatched.
    """

    def __init__(self, *, narrator: DecisionNarrator, orchestrator):
        self.narrator = narrator
        self.orchestrator = orchestrator

    def dispatch(self, decision: Dict[str, Any]) -> None:
        # 🧠 Let the system narrate itself first
        canonical_decision = self.narrator.narrate(decision)

        # 📦 Then pass to the existing orchestrator
        self.orchestrator.dispatch(canonical_decision)
