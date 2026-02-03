# trading_core/risk/market_risk_snapshot.py

from dataclasses import dataclass
from typing import Dict
import math


@dataclass
class MarketRiskSnapshot:
    """
    Continuous Risk Field Snapshot
    所有欄位皆為連續值（0~∞），不做區間切割
    """
    rsi_pressure: float          # 動能壓力（0~1）
    atr_pressure: float          # 波動壓力（>1 = 高於常態）
    volatility_pressure: float   # 不確定性密度
    liquidity_pressure: float    # 流動性緊張程度
    
    # 🆕 結構風險（來自均線）
    structure_tension: float       # 均線之間的張力（距離總和）
    structure_directionality: float # 結構方向一致性（斜率一致程度）
    composite_risk: float        # 綜合風險指數（僅供參考）


def safe_div(a: float, b: float, default: float = 0.0) -> float:
    if b == 0 or b is None or math.isnan(b):
        return default
    return a / b


def build_market_risk_snapshot(indicators: Dict) -> MarketRiskSnapshot:
    """
    將技術指標轉為「風險場描述」
    indicators: 來自 analysis / indicator layer 的原始指標
    """

    # === RSI 壓力：偏離中性越遠，壓力越大 ===
    rsi = indicators.get("rsi")
    if rsi is None:
        rsi_pressure = 0.0
    else:
        rsi_pressure = abs(rsi - 50.0) / 50.0   # 0 ~ 1+

    # === ATR 壓力：相對於價格的呼吸幅度 ===
    atr = indicators.get("atr")
    price = indicators.get("price")
    atr_pressure = safe_div(atr, price, 0.0)

    # === 波動壓力：ATR 相對歷史均值 ===
    atr_mean = indicators.get("atr_mean")  # 可之後補 rolling
    volatility_pressure = safe_div(atr, atr_mean, 1.0)

    # === 流動性壓力：成交量異常程度 ===
    vol_ratio = indicators.get("vol_ratio", 1.0)
    liquidity_pressure = max(0.0, vol_ratio - 1.0)
    # === 均線結構張力（structure tension）===
    dist_sm = indicators.get("ema_dist_sm", 0.0)
    dist_ml = indicators.get("ema_dist_ml", 0.0)

    structure_tension = abs(dist_sm) + abs(dist_ml)

    # === 均線方向一致性（structure directionality）===
    slopes = [
        indicators.get("ema_short_slope"),
        indicators.get("ema_mid_slope"),
        indicators.get("ema_long_slope"),
    ]

    # 移除 None
    slopes = [s for s in slopes if s is not None]

    if len(slopes) >= 2:
        same_sign = sum(
            1 for s in slopes
            if s * slopes[0] > 0
        )
        structure_directionality = same_sign / len(slopes)
    else:
        structure_directionality = 0.0
    # === 綜合風險（不做 hard rule）===
    composite = (
        0.30 * rsi_pressure +
        0.25 * volatility_pressure +
        0.15 * atr_pressure +
        0.10 * liquidity_pressure +
        0.10 * structure_tension +
        0.10 * structure_directionality
    )

    return MarketRiskSnapshot(
        rsi_pressure=float(rsi_pressure),
        atr_pressure=float(atr_pressure),
        volatility_pressure=float(volatility_pressure),
        liquidity_pressure=float(liquidity_pressure),

        structure_tension=float(structure_tension),
        structure_directionality=float(structure_directionality),

        composite_risk=float(composite),
    )

