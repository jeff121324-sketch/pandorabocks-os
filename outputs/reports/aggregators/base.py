# aisop/outputs/reports/aggregators/base.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseAggregator(ABC):
    """
    Base class for time-based aggregators (weekly / monthly).

    ⚠️ Rules:
    - Read-only
    - No side effects
    - No event bus
    - No governance mutation
    """

    def __init__(self, decisions: List[Dict[str, Any]]):
        self.decisions = decisions

    @abstractmethod
    def aggregate(self) -> Dict[str, Any]:
        """
        Aggregate decisions into a summarized structure.
        """
        raise NotImplementedError
