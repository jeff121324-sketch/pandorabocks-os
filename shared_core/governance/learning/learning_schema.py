# shared_core/governance/learning/learning_schema.py

from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass(frozen=True)
class LearningRequest:
    """
    Governance-level learning request.
    No execution implied.
    """
    persona: str
    requested_at: datetime
    reasons: List[str]
    suggested_scope: str   # short / mid / long
    priority: str          # low / medium / high
