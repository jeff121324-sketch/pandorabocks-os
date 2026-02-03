# trading_core/analysis/indicators/volume.py
import pandas as pd
import numpy as np
import ta

def compute_volume(df: pd.DataFrame) -> dict:
    if df is None or df.empty:
        return {}

    vol = df["volume"]
    close = df["close"]

    # === OBV ===
    obv = ta.volume.OnBalanceVolumeIndicator(close, vol).on_balance_volume()

    # === Volume MA ===
    vol_ma = vol.rolling(20).mean()

    # === VWAP ===
    cum_vol = vol.cumsum()
    vwap = (
        float((close * vol).cumsum().iloc[-1] / cum_vol.iloc[-1])
        if cum_vol.iloc[-1] > 0 else np.nan
    )

    return {
        "volume": float(vol.iloc[-1]),
        "vol_ratio": float(vol.iloc[-1] / vol_ma.iloc[-1])
        if len(df) >= 20 and vol_ma.iloc[-1] > 0 else np.nan,
        "obv": float(obv.iloc[-1]) if not obv.empty else np.nan,
        "obv_slope": float(obv.diff().iloc[-1])
        if len(obv) > 1 else np.nan,
        "vwap": vwap,
    }