from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass(frozen=True)
class PersonaDecisionRecord:
    """
    Immutable record of ONE persona decision behavior.
    This is the atomic unit for Arbiter evaluation.
    """

    # Identity
    persona: str                      # attacker / defender / balancer / future
    agenda_id: str
    proposal_id: str

    # Decision behavior
    stance: str                       # approve / reject / abstain
    confidence: float                # persona self-confidence at decision time

    # Outcome reference
    final_outcome: str                # approved / rejected / deferred

    # Temporal
    decided_at: datetime

    # Derived tags (filled by Arbiter, not persona)
    alignment: Optional[float] = None
    """
    How aligned confidence & stance were with final outcome.
    Range suggestion: -1.0 ~ +1.0
    """

    risk_notes: Optional[List[str]] = None
    """
    Arbiter annotations, e.g.:
    - 'low_confidence_execution'
    - 'overconfident_miss'
    - 'abstain_correctly'
    """
# === Phase 3-B: performance window ===

@dataclass(frozen=True)
class PersonaPerformanceWindow:
    persona: str
    window_type: str                  # short / mid / long
    records: List[PersonaDecisionRecord]

    average_confidence: float
    alignment_score: float
    abstain_rate: float
    execution_rate: float

    warning_flags: List[str]


# === Phase 3-C: trust snapshot ===

@dataclass(frozen=True)
class PersonaTrustSnapshot:
    persona: str
    snapshot_at: datetime

    trust_score: float
    stability_score: float
    learning_integrity: float

    status_flags: List[str]
    notes: Optional[str] = None