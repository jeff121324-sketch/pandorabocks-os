# aisop_core/learning/learning_request_handler.py

from shared_core.governance.learning.learning_schema import LearningRequest
from shared_core.governance.arbiter.schema import PersonaTrustSnapshot

from .learning_policy import LearningPolicy, LearningDecision


class LearningRequestHandler:
    """
    Level 1 Learning Handler

    - Accepts LearningRequest
    - Applies LearningPolicy
    - Does NOT execute learning
    """

    def __init__(self):
        self.policy = LearningPolicy()

    def handle(
        self,
        request: LearningRequest,
        snapshot: PersonaTrustSnapshot,
    ) -> LearningDecision:
        return self.policy.evaluate(request, snapshot)

class PersonaTrustSnapshot:
    def __init__(self):
        self.trust = {}

    def get_trust(self, persona_name: str) -> float:
        return 1.0  # v0：全部人格等權