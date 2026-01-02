# aisop_core/reflection/reflection_prompt_builder.py

from typing import List

from shared_core.governance.arbiter.schema import (
    PersonaDecisionRecord,
    PersonaPerformanceWindow,
    PersonaTrustSnapshot,
)


class ReflectionPromptBuilder:
    """
    Builds reflection questions only.
    No suggestions, no actions.
    """

    def build(
        self,
        records: List[PersonaDecisionRecord],
        window: PersonaPerformanceWindow,
        snapshot: PersonaTrustSnapshot,
    ) -> List[str]:
        prompts: List[str] = []

        if window.average_confidence > 0.7 and window.alignment_score < 0:
            prompts.append(
                "In which situations do I tend to be overconfident but misaligned?"
            )

        if snapshot.stability_score < 0.4:
            prompts.append(
                "Have my decision patterns drifted over time without awareness?"
            )

        if snapshot.trust_score < 0.3:
            prompts.append(
                "Which assumptions repeatedly led to low-trust outcomes?"
            )

        if not prompts:
            prompts.append(
                "Are there any subtle patterns in my recent decisions worth reviewing?"
            )

        return prompts
