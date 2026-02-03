# trading_core/personas/context_profile.py

from dataclasses import dataclass
from typing import Tuple

@dataclass
class ContextProfile:
    price_change_range: Tuple[float, float]
    risk_levels: Tuple[str, ...]
    volatility_preference: str  # "low" | "mid" | "high"
