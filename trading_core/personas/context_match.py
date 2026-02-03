# trading_core/personas/context_match.py

from .context_profile import ContextProfile


def score_context(profile: ContextProfile, payload: dict) -> float:
    """
    Returns a context match score in [0, 1].
    Deterministic, no history, no ML.
    """

    score = 1.0

    change = abs(payload.get("change", 0.0))
    risk = payload.get("risk_level", "low")

    low, high = profile.price_change_range
    if not (low <= change <= high):
        score *= 0.5

    # ✅ 這行改成 risk_levels（跟 ContextProfile 對齊）
    if risk not in profile.risk_levels:
        score *= 0.4

    return round(score, 3)
