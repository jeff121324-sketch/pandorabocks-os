# shared_core/governance/decision_personas/base.py
from abc import ABC, abstractmethod
from .schema import DecisionSummary, PersonaOpinion
from shared_core.governance.parliament.context import GovernanceContext


class DecisionPersona(ABC):
    """
    Decision Persona Base
    - Pure evaluation
    - No side effects
    - No voting
    """
    name: str

    @abstractmethod
    def evaluate(
        self,
        summary: DecisionSummary,
        context: GovernanceContext,
    ) -> PersonaOpinion:
        raise NotImplementedError
