# shared_core/governance/context.py

# shared_core/governance/context.py

from collections import deque
from typing import Deque, List


class GovernanceContext:
    """
    Governance v0.5 Context

    Responsibilities:
    - World capability boundary
    - Recent decision history (stability)
    - Governance-level risk & state judgement
    """

    def __init__(
        self,
        world_capabilities: List[str],
        decision_history: Deque | None = None,
        high_risk: bool = False,
    ):
        self.world_capabilities = set(world_capabilities)

        # 決策歷史（由 GovernanceRuntime 統一寫入）
        self._decision_history: Deque = (
            decision_history if decision_history is not None else deque(maxlen=20)
        )

        # 世界風險旗標（v0.5：人工或設定檔指定）
        self._high_risk = high_risk

    # =========================================================
    # Stability Guard
    # =========================================================
    def is_flapping(self, proposal_id: str) -> bool:
        """
        Detect decision flapping for a given proposal_id.
        """
        recent = [
            d.outcome
            for d in self.recent_decisions()
            if d.proposal_id == proposal_id
        ]
    
        if len(recent) < 3:
            return False

        # 出現來回翻轉（例如 approve → reject → approve）
        return len(set(recent[-3:])) > 1

    # =========================================================
    # Risk Guard
    # =========================================================
    def is_high_risk_world(self) -> bool:
        """
        高風險世界 → Arbiter 預設保守
        """
        return self._high_risk

    # =========================================================
    # Decision History Management
    # =========================================================
    def record_decision(self, decision) -> None:
        """
        GovernanceRuntime 在 decision 落盤時呼叫
        """
        self._decision_history.append(decision)

    def recent_decisions(self, limit: int = 5):
        return list(self._decision_history)[-limit:]

    # =========================================================
    # Debug / Introspection
    # =========================================================
    def summary(self) -> dict:
        return {
            "world_capabilities": sorted(self.world_capabilities),
            "high_risk": self._high_risk,
            "recent_decisions": [
                {
                    "proposal_id": d.proposal_id,
                    "outcome": d.outcome,
                    "notes": d.notes,
                }
                for d in self.recent_decisions()
            ],
        }

