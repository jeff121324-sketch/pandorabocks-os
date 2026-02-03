# trading_core/analysis/indicators/volatility.py
import pandas as pd
import numpy as np
import ta

def compute_volatility(df: pd.DataFrame) -> dict:
    if df is None or df.empty:
        return {}

    w_atr = 14
    w_bb = 20
    close = df["close"]

    # === ATR ===
    if len(df) < w_atr:
        atr_val = np.nan
    else:
        atr_series = ta.volatility.AverageTrueRange(
            high=df["high"],
            low=df["low"],
            close=close,
            window=w_atr,
        ).average_true_range()
        atr_val = float(atr_series.iloc[-1])

    # === Bollinger Bands ===
    if len(df) < w_bb:
        bb_width = np.nan
    else:
        bb = ta.volatility.BollingerBands(close, window=w_bb)
        bb_width = float(
            bb.bollinger_hband().iloc[-1] - bb.bollinger_lband().iloc[-1]
        )

    return {
        "atr": atr_val,
        "atr_pct": atr_val / close.iloc[-1]
        if not np.isnan(atr_val) else np.nan,
        "bb_width": bb_width,
    }