# aisop_core/reflection/self_review_engine.py

from typing import List

from shared_core.governance.arbiter.schema import (
    PersonaDecisionRecord,
    PersonaPerformanceWindow,
    PersonaTrustSnapshot,
)

from .reflection_prompt_builder import ReflectionPromptBuilder


class SelfReviewEngine:
    """
    Level 1 Reflection Engine

    - Aggregates data
    - Produces reflection prompts
    - No behavior modification
    """

    def __init__(self):
        self.builder = ReflectionPromptBuilder()

    def review(
        self,
        records: List[PersonaDecisionRecord],
        window: PersonaPerformanceWindow,
        snapshot: PersonaTrustSnapshot,
    ) -> List[str]:
        return self.builder.build(records, window, snapshot)
