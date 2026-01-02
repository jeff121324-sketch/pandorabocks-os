# shared_core/governance/decision_api.py
from typing import List
from shared_core.governance.parliament.context import GovernanceContext
from .decision_personas.schema import DecisionSummary, PersonaOpinion
from .decision_personas.attacker import AttackerDecisionPersona
from .decision_personas.defender import DefenderDecisionPersona
from .decision_personas.balancer import BalancerDecisionPersona


class DecisionAPI:
    """
    Facade for project-level decision request.
    """

    def __init__(self):
        self._personas = [
            AttackerDecisionPersona(),
            DefenderDecisionPersona(),
            BalancerDecisionPersona(),
        ]

    def request_opinions(
        self,
        summary: DecisionSummary,
        context: GovernanceContext,
    ) -> List[PersonaOpinion]:
        """
        Project-facing API.
        Returns persona opinions (NOT votes).
        """
        opinions: List[PersonaOpinion] = []

        for persona in self._personas:
            opinion = persona.evaluate(summary, context)
            opinions.append(opinion)

        return opinions
