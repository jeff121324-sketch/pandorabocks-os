# trading_core/analysis/indicators/trend.py
import pandas as pd
import numpy as np
import ta

def compute_trend(df: pd.DataFrame) -> dict:
    if df is None or df.empty:
        return {}

    close = df["close"]

    # === 均線 window ===
    w_short = 5
    w_mid = 20
    w_long = 60
    w_adx = 14
    min_len_adx = w_adx * 2
    # === EMA ===
    ma_short = ta.trend.EMAIndicator(close, window=w_short).ema_indicator()
    ma_mid   = ta.trend.EMAIndicator(close, window=w_mid).ema_indicator()
    ma_long  = ta.trend.EMAIndicator(close, window=w_long).ema_indicator()

    def slope(series):
        if series.isna().all() or len(series) < 2:
            return np.nan
        return float(series.iloc[-1] - series.iloc[-2])

    # === EMA distance（不足時給 NaN）===
    dist_sm = (
        float(ma_short.iloc[-1] - ma_mid.iloc[-1])
        if len(df) >= w_mid else np.nan
    )
    dist_ml = (
        float(ma_mid.iloc[-1] - ma_long.iloc[-1])
        if len(df) >= w_long else np.nan
    )

    # === ADX（最容易炸的地方）===
    if len(df) < min_len_adx:
        adx_val = np.nan
    else:
        adx_series = ta.trend.ADXIndicator(
            high=df["high"],
            low=df["low"],
            close=close,
            window=w_adx,
        ).adx()
        adx_val = float(adx_series.iloc[-1])

    return {
        "ema_short": float(ma_short.iloc[-1]) if len(df) >= w_short else np.nan,
        "ema_mid":   float(ma_mid.iloc[-1])   if len(df) >= w_mid else np.nan,
        "ema_long":  float(ma_long.iloc[-1])  if len(df) >= w_long else np.nan,

        "ema_short_slope": slope(ma_short),
        "ema_mid_slope":   slope(ma_mid),
        "ema_long_slope":  slope(ma_long),

        "ema_dist_sm": dist_sm,
        "ema_dist_ml": dist_ml,

        "adx": adx_val,
        "trend_clarity": adx_val / 50.0 if not np.isnan(adx_val) else np.nan,
        # === ✅ 制度型指標（給 World / Regime 用）===
        "ema_20": float(ma_mid.iloc[-1]) if len(df) >= w_mid else np.nan,
        "ema_50": float(ma_long.iloc[-1]) if len(df) >= w_long else np.nan,
        "ema_200": float(
            ta.trend.EMAIndicator(close, window=200).ema_indicator().iloc[-1]
        ) if len(df) >= 200 else np.nan,
    }