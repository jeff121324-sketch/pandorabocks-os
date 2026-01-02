# shared_core/governance/decision_personas/schema.py
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class DecisionSummary:
    """
    Project → Governance input.
    專案只能給『摘要』，不能給結論。
    """
    source_project: str          # e.g. "aisop-hotel"
    subject: str                 # e.g. "front_desk_staffing"
    intent: str                  # e.g. "increase_staff"
    time_scope: str              # short / mid / long
    risk_flags: List[str]        # project-perceived risks
    confidence_hint: float       # project self-confidence (0~1)


@dataclass(frozen=True)
class PersonaOpinion:
    """
    Decision persona opinion (NOT a Vote).
    """
    persona: str                 # attacker / defender / balancer
    stance: str                  # approve / reject / abstain
    confidence: float            # persona self-confidence
    rationale: str               # short explanation
