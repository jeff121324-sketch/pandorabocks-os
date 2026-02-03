# trading_core/state/trade_attempt.py

from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class TradeAttempt:
    attempt_id: int
    episode_id: int
    timestamp: float

    personas: Dict[str, Any]        # attacker / defender / balancer
    gate_result: str                # ALLOW / BLOCK
    gate_reason: str

    proposed_action: str            # long / short / abstain
    confidence: float

    is_executable: bool             # gate_result == ALLOW
    would_execute_if_live: bool     # TRAINING semantic

    regime: str
    training: bool = True
