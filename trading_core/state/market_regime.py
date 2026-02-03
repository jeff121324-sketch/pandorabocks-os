# trading_core/state/market_regime.py

from dataclasses import dataclass
from typing import Literal


RegimeType = Literal[
    "NEUTRAL",
    "TRENDING",
    "VOLATILE",
    "BREAKOUT",
]


@dataclass(frozen=True)
class MarketRegimeSnapshot:
    regime: RegimeType
    tradable: bool
    confidence: float
    rationale: str

def build_market_regime(indicator_snapshot, perception_health):
    """
    Build MarketRegimeSnapshot from indicator snapshot and perception health.

    - Compatible with Live (object-based) and Audit (dict-based) inputs
    - No side effects
    - Deterministic
    """

    # -------------------------------------------------
    # 1️⃣ Perception health（相容 object / dict）
    # -------------------------------------------------
    is_healthy = (
        perception_health.is_healthy
        if hasattr(perception_health, "is_healthy")
        else perception_health.get("is_healthy", False)
    )

    if not is_healthy:
        return MarketRegimeSnapshot(
            regime="NEUTRAL",
            tradable=False,
            confidence=0.0,
            rationale="perception health check failed",
        )

    # -------------------------------------------------
    # 2️⃣ Indicator snapshot（相容 object / dict）
    # -------------------------------------------------
    def _get(snapshot, key, default=None):
        if hasattr(snapshot, key):
            return getattr(snapshot, key)
        if isinstance(snapshot, dict):
            return snapshot.get(key, default)
        return default

    trend = _get(indicator_snapshot, "trend_strength", 0)
    volatility = _get(indicator_snapshot, "volatility", 0)
    volatility_mean = _get(indicator_snapshot, "volatility_mean", volatility)
    compression = _get(indicator_snapshot, "volatility_compressed", False)

    # -------------------------------------------------
    # 4️⃣ 自由型趨勢判斷（完全容忍缺失維度）
    # -------------------------------------------------

    # 可用性判斷
    trend_available = trend is not None
    volatility_available = volatility is not None

    # 趨勢是否開始有存在感
    trend_present = trend_available and trend > 18

    # 是否脫離壓縮狀態（壓縮本身可能是 None）
    compression_releasing = (compression is False)

    # 世界對趨勢成立的信心（連續、只用可用資訊）
    trend_score = 0.0
    weight = 0.0

    if trend_available:
        weight += 0.5
        if trend_present:
            trend_score += 0.5

    if volatility_available:
        weight += 0.3
        # 有 volatility 就給存在分，不判斷大小
        trend_score += 0.3

    # compression 是 bonus，不是必要條件
    if compression_releasing:
        weight += 0.2
        trend_score += 0.2

    # 正規化（避免某些維度缺失時分數過低）
    normalized_score = trend_score / weight if weight > 0 else 0.0

    if normalized_score >= 0.6:
        return MarketRegimeSnapshot(
            regime="TRENDING",
            tradable=True,
            confidence=round(normalized_score, 2),
            rationale=(
                f"score={normalized_score:.2f} | "
                f"trend={trend}, "
                f"vol={volatility}, "
                f"compression={compression}"
            ),
        )

    # -------------------------------------------------
    # 5️⃣ 預設：保守中性
    # -------------------------------------------------
    return MarketRegimeSnapshot(
        regime="NEUTRAL",
        tradable=False,
        confidence=0.5,
        rationale="no clear regime detected",
    )
