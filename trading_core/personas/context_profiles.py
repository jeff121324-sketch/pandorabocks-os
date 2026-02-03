# trading_core/personas/context_profiles.py

from .context_profile import ContextProfile

ATTACKER_CONTEXT = ContextProfile(
    price_change_range=(0.003, 0.02),
    risk_levels=("low", "medium"),
    volatility_preference="high",
)

BALANCER_CONTEXT = ContextProfile(
    price_change_range=(0.002, 0.008),
    risk_levels=("low", "medium"),
    volatility_preference="mid",
)

DEFENDER_CONTEXT = ContextProfile(
    price_change_range=(0.0, 0.006),
    risk_levels=("medium", "high"),
    volatility_preference="low",
)
