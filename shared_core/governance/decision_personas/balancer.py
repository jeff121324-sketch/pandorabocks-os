# shared_core/governance/decision_personas/balancer.py
from .base import DecisionPersona
from .schema import DecisionSummary, PersonaOpinion


class BalancerDecisionPersona(DecisionPersona):
    name = "balancer"

    def evaluate(self, summary: DecisionSummary, context) -> PersonaOpinion:
        if summary.time_scope == "long":
            return PersonaOpinion(
                persona=self.name,
                stance="abstain",
                confidence=0.6,
                rationale="long-term decision requires stability",
            )

        return PersonaOpinion(
            persona=self.name,
            stance="approve",
            confidence=0.55,
            rationale="balanced default stance",
        )
