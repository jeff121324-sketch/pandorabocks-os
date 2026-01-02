# shared_core/governance/decision_personas/attacker.py
from .base import DecisionPersona
from .schema import DecisionSummary, PersonaOpinion


class AttackerDecisionPersona(DecisionPersona):
    name = "attacker"

    def evaluate(self, summary: DecisionSummary, context) -> PersonaOpinion:
        if summary.time_scope == "short" and summary.confidence_hint >= 0.6:
            return PersonaOpinion(
                persona=self.name,
                stance="approve",
                confidence=0.6,
                rationale="short-term upside acceptable",
            )

        return PersonaOpinion(
            persona=self.name,
            stance="abstain",
            confidence=0.4,
            rationale="not a clear opportunity",
        )
