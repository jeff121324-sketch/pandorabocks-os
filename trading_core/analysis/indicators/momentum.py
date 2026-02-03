# trading_core/analysis/indicators/momentum.py
import pandas as pd
import numpy as np
import ta

def compute_momentum(df: pd.DataFrame) -> dict:
    if df is None or df.empty:
        return {}

    close = df["close"]

    w_rsi = 14

    # === RSI ===
    if len(df) < w_rsi:
        rsi_val = np.nan
        rsi_slope = np.nan
    else:
        rsi_series = ta.momentum.RSIIndicator(close, window=w_rsi).rsi()
        rsi_val = float(rsi_series.iloc[-1])
        rsi_slope = float(rsi_series.diff().iloc[-1])

    # === MACD（需要更長資料，但 ta 會自己處理）===
    macd = ta.trend.MACD(close)
    macd_val = macd.macd().iloc[-1]
    macd_hist = macd.macd_diff().iloc[-1]

    # === Stochastic ===
    if len(df) < w_rsi:
        k = d = j = np.nan
    else:
        stoch = ta.momentum.StochasticOscillator(
            high=df["high"], low=df["low"], close=close
        )
        k = float(stoch.stoch().iloc[-1])
        d = float(stoch.stoch_signal().iloc[-1])
        j = 3 * k - 2 * d

    return {
        "rsi": rsi_val,
        "rsi_slope": rsi_slope,
        "macd": float(macd_val),
        "macd_hist": float(macd_hist),
        "kdj_k": k,
        "kdj_d": d,
        "kdj_j": j,
    }