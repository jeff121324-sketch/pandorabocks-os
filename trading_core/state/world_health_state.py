# trading_core/state/world_health_state.py

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class WorldHealthLevel(str, Enum):
    """
    World-level health classification.
    """
    HEALTHY = "healthy"       # 完全可信
    DEGRADED = "degraded"     # 有裂痕，但仍可運作
    UNTRUSTED = "untrusted"   # 不可自動決策


@dataclass(frozen=True)
class WorldHealthState:
    """
    Immutable snapshot of world health state.
    """
    level: WorldHealthLevel
    reasons: List[str] = field(default_factory=list)

    def is_healthy(self) -> bool:
        return self.level == WorldHealthLevel.HEALTHY

    def is_degraded(self) -> bool:
        return self.level == WorldHealthLevel.DEGRADED

    def is_untrusted(self) -> bool:
        return self.level == WorldHealthLevel.UNTRUSTED