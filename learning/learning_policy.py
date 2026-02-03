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
    def evaluate(
        self,
        request: LearningRequest,
        snapshot: PersonaTrustSnapshot | None,
    ) -> LearningDecision:

        # Learning v0：不使用 trust snapshot
        if snapshot is None:
            return LearningDecision(
                accepted=True,
                reason="learning_v0_observation_only",
            )

        # （v1 以後才會走到下面）
        return LearningDecision(
            accepted=True,
            reason="learning_allowed_by_policy",
        )