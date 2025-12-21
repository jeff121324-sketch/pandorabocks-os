"""
Parliament Schema v0.1
=====================

設計原則：
- 不依賴任何既有 trading / persona / AI 模組
- 純資料結構（不可變語意）
- 天生支援多 Agenda 並行
- 可被 Event / Library / Replay 安全使用

本檔只定義『制度語言』，不包含任何決策智慧。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Literal, Optional
from datetime import datetime
from dataclasses import asdict

# =============================
# Core Primitive: Agenda
# =============================

@dataclass(frozen=True)
class Agenda:
    """
    一個 Agenda 代表一次獨立、可審計的決策上下文。
    所有 Proposal / Vote / Decision 都必須綁定 agenda_id。
    """
    agenda_id: str
    context: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.utcnow)


# =============================
# Proposal
# =============================

@dataclass(frozen=True)
class Proposal:
    """
    議會的提案單位。
    只描述『想做什麼』與『限制條件』，不描述怎麼做。
    """
    agenda_id: str
    proposal_id: str
    proposer_role: str
    action: Dict[str, Any]
    constraints: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


# =============================
# Vote
# =============================

VoteStance = Literal["approve", "reject", "abstain"]

@dataclass(frozen=True)
class Vote:
    """
    單一制度角色對 Proposal 的正式表態。
    """
    agenda_id: str
    proposal_id: str
    role: str
    stance: VoteStance
    confidence: float
    rationale: str
    created_at: datetime = field(default_factory=datetime.utcnow)


# =============================
# Decision
# =============================

DecisionOutcome = Literal["approved", "rejected", "deferred"]

@dataclass(frozen=True)
class Decision:
    """
    議會的制度性結論。
    Decision ≠ Execution，只代表制度結果。
    """
    agenda_id: str
    proposal_id: str
    outcome: DecisionOutcome
    votes: List[Vote]
    arbitration_required: bool = False
    notes: Optional[str] = None
    decided_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize Decision into a pure dict for audit / library / replay.
        Side-effect free and JSON-safe.
        """
        return {
            "agenda_id": self.agenda_id,
            "proposal_id": self.proposal_id,
            "outcome": self.outcome,
            "arbitration_required": self.arbitration_required,
            "notes": self.notes,
            "decided_at": self.decided_at.isoformat(),
            "votes": [
                {
                    "role": v.role,
                    "stance": v.stance,
                    "confidence": v.confidence,
                    "rationale": v.rationale,
                }
                for v in self.votes
            ],
        }
