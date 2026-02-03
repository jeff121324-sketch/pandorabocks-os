# aisop/learning/learning_request_adapter.py

from datetime import datetime
from shared_core.governance.learning.learning_schema import LearningRequest

def build_learning_request(
    snapshot: dict,
    regime,
    personas: dict,
    timestamp: float,
) -> LearningRequest:
    """
    Build a governance-level LearningRequest
    from Trading World observation (Learning v0).
    """

    reasons = []

    # 世界理由
    if regime.tradable:
        reasons.append("market_tradable")

    if snapshot.get("trend_strength", 0) > 20:
        reasons.append("trend_emerging")

    # 人格理由（只挑有發言的）
    for name, p in personas.items():
        if p is not None and p.get("confidence", 0) > 0.6:
            reasons.append(f"{name}_high_confidence")

    # v0 防呆：沒有理由就不送學習請求
    if not reasons:
        reasons.append("exploratory_observation")

    return LearningRequest(
        persona="trading_world",   # 不是 attacker / defender
        requested_at=datetime.utcfromtimestamp(timestamp),
        reasons=reasons,
        suggested_scope="short",   # v0 固定
        priority="low",            # v0 固定
    )
