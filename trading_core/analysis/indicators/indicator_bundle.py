# trading_core/analysis/indicators/indicator_bundle.py
import pandas as pd

from .momentum import compute_momentum
from .trend import compute_trend
from .volatility import compute_volatility
from .volume import compute_volume

def build_indicator_bundle(df: pd.DataFrame) -> dict:
    """
    統一出口：永遠回傳 dict
    - 指標可失敗
    - price 不可缺席
    """
    indicators = {}

    # --- 1️⃣ 安全檢查 ---
    if df is None or len(df) == 0:
        return {"price": None}

    # --- 2️⃣ price 是世界基準，優先處理 ---
    try:
        indicators["price"] = float(df["close"].iloc[-1])
    except Exception as e:
        print(f"[IndicatorBundle] ⚠️ price unavailable: {e}")
        indicators["price"] = None

    # --- 3️⃣ 其餘指標：可選、可失敗 ---
    try:
        indicators.update(compute_momentum(df))
    except Exception as e:
        print(f"[IndicatorBundle] ⚠️ momentum failed: {e}")

    try:
        indicators.update(compute_trend(df))
    except Exception as e:
        print(f"[IndicatorBundle] ⚠️ trend failed: {e}")

    try:
        indicators.update(compute_volatility(df))
    except Exception as e:
        print(f"[IndicatorBundle] ⚠️ volatility failed: {e}")

    try:
        indicators.update(compute_volume(df))
    except Exception as e:
        print(f"[IndicatorBundle] ⚠️ volume failed: {e}")

    return indicators

def build_indicator_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    total = len(df)

    for i in range(total):
        if i % 500 == 0:
            print(f"⏳ processing {i}/{total}")

        sub_df = df.iloc[: i + 1]
        snapshot = {}
        snapshot.update(compute_momentum(sub_df))
        snapshot.update(compute_trend(sub_df))
        snapshot.update(compute_volatility(sub_df))
        snapshot.update(compute_volume(sub_df))
        rows.append(snapshot)

    return pd.DataFrame(rows)