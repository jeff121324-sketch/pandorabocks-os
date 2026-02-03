from enum import Enum


class MacroTrend(Enum):
    ALIVE = "alive"
    DEAD = "dead"
    UNKNOWN = "unknown" 

class DistributionStage(Enum):
    NONE = "none"
    EARLY = "early"
    CONFIRMED = "confirmed"


class CapitalPosture(Enum):
    RISK_ON = "risk_on"
    NEUTRAL = "neutral"
    CASH_BIASED = "cash_biased"
