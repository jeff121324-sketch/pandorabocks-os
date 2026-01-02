# shared_core/governance/chair/chair_supervisor.py

from dataclasses import dataclass
from typing import List

from shared_core.governance.arbiter.schema import PersonaTrustSnapshot


@dataclass(frozen=True)
class ChairDirective:
    """
    Chair 的輸出不是命令，是治理要求。
    """
    persona: str
    action: str           # request_learning / continue / observe
    reasons: List[str]


class ChairSupervisor:
    """
    Chair = 人格監管者
    只讀信任狀態，不介入決策。
    """

    def review(self, snapshot: PersonaTrustSnapshot) -> ChairDirective:
        reasons: List[str] = []

        # -------------------------
        # Learning integrity check
        # -------------------------
        if snapshot.learning_integrity < 0.4:
            reasons.append("learning_integrity_degraded")

        # -------------------------
        # Trust level check
        # -------------------------
        if snapshot.trust_score < 0.3:
            reasons.append("low_trust_level")

        # -------------------------
        # Stability check
        # -------------------------
        if snapshot.stability_score < 0.3:
            reasons.append("behavior_drift_detected")

        # -------------------------
        # Decide chair action
        # -------------------------
        if reasons:
            action = "request_learning"
        else:
            action = "continue"

        return ChairDirective(
            persona=snapshot.persona,
            action=action,
            reasons=reasons,
        )
