# shared_core/governance/parliament_adapter.py
from typing import List
from uuid import uuid4

from shared_core.governance.parliament.parliament_schema import (
    Proposal,
    Vote,
)
from shared_core.governance.decision_personas.schema import (
    DecisionSummary,
    PersonaOpinion,
)
from shared_core.governance.parliament.context import GovernanceContext


class ParliamentAdapter:
    """
    Adapter layer:
    PersonaOpinion -> Vote -> ParliamentEngine
    """

    def __init__(self, engine):
        self.engine = engine

    def submit_decision(
        self,
        *,
        summary: DecisionSummary,
        opinions: List[PersonaOpinion],
        context: GovernanceContext,
    ):
        """
        Create Proposal + Votes, submit to ParliamentEngine.
        """

        agenda_id = f"decision-{summary.source_project}"
        proposal_id = str(uuid4())

        # -----------------------------
        # Proposal（制度語言）
        # -----------------------------
        proposal = Proposal(
            agenda_id=agenda_id,
            proposal_id=proposal_id,
            proposer_role="decision_api",
            action={
                "subject": summary.subject,
                "intent": summary.intent,
                "time_scope": summary.time_scope,
            },
            constraints={
                # GovernanceContext already has world_capabilities
                "world_capabilities": list(context.world_capabilities),
            },
        )

        # -----------------------------
        # Votes（只來自決策人格）
        # -----------------------------
        votes: List[Vote] = []

        for op in opinions:
            votes.append(
                Vote(
                    agenda_id=agenda_id,
                    proposal_id=proposal_id,
                    role=op.persona,               # attacker / defender / balancer
                    stance=op.stance,              # approve / reject / abstain
                    confidence=op.confidence,      # persona self-confidence
                    rationale=op.rationale,
                )
            )

        # -----------------------------
        # Parliament evaluation
        # -----------------------------
        decision = self.engine.evaluate(
            proposal=proposal,
            votes=votes,
        )

        return decision
