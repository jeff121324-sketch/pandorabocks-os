# shared_core/governance/decision_personas/defender.py
from .base import DecisionPersona
from .schema import DecisionSummary, PersonaOpinion


class DefenderDecisionPersona(DecisionPersona):
    name = "defender"

    def evaluate(self, summary: DecisionSummary, context) -> PersonaOpinion:
        if summary.risk_flags:
            return PersonaOpinion(
                persona=self.name,
                stance="reject",
                confidence=0.7,
                rationale="risk flags present",
            )

        return PersonaOpinion(
            persona=self.name,
            stance="abstain",
            confidence=0.5,
            rationale="no explicit risk detected",
        )
