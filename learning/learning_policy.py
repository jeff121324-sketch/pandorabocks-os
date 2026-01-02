# aisop_core/learning/learning_policy.py

from dataclasses import dataclass
from typing import List

from shared_core.governance.learning.learning_schema import LearningRequest
from shared_core.governance.arbiter.schema import PersonaTrustSnapshot


@dataclass(frozen=True)
class LearningDecision:
    """
    Administrative decision, NOT execution.
    """
    accepted: bool
    reason: str


class LearningPolicy:
    """
    Learning Policy (Level 1)

    - Can ACCEPT or REJECT learning requests
    - Does NOT train
    - Does NOT modify personas
    """

    def evaluate(
        self,
        request: LearningRequest,
        snapshot: PersonaTrustSnapshot,
    ) -> LearningDecision:
        # Rule 1: insufficient trust data
        if snapshot.trust_score == 0.0 and snapshot.stability_score == 0.0:
            return LearningDecision(
                accepted=False,
                reason="insufficient_long_term_data",
            )

        # Rule 2: learning integrity too low (possible exploitation)
        if snapshot.learning_integrity < 0.3:
            return LearningDecision(
                accepted=False,
                reason="learning_integrity_too_low",
            )

        # Rule 3: default allow (still no execution)
        return LearningDecision(
            accepted=True,
            reason="learning_allowed_by_policy",
        )
