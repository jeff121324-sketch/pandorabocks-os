import sys
from pathlib import Path
from datetime import datetime, timezone

# === 專案根目錄（aisop/） ===
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
from pathlib import Path

from trading_core.analysis.indicators.indicator_bundle import build_indicator_dataframe
from trading_core.analysis.indicators.indicator_csv_writer import IndicatorCSVWriter


def sanitize_kline_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    將原始 K 線資料清洗為「可計算、可被信任」的狀態
    這一步是必要的，不是 workaround
    """

    # 1️⃣ 強制數值欄位型別
    numeric_cols = ["open", "high", "low", "close", "volume"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 2️⃣ 時間欄位處理（依你實際資料存在的欄位）
    if "ts" in df.columns:
        df["ts"] = pd.to_numeric(df["ts"], errors="coerce")
        df = df.sort_values("ts")
        df = df.drop_duplicates(subset=["ts"], keep="last")

    elif "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
        df = df.sort_values("datetime")
        df = df.drop_duplicates(subset=["datetime"], keep="last")

    # 3️⃣ 移除不完整的 K 線
    df = df.dropna(subset=["open", "high", "low", "close"])

    # 4️⃣ reset index，避免 concat 對齊問題
    df = df.reset_index(drop=True)

    return df


def run_batch(
    csv_path: str,
    out_path: str,
    interval: str,
):
    print(f"[RUN] Indicator batch start | interval={interval}")

    # 1️⃣ 讀原始 K 線（關掉 low_memory，避免 dtype 混亂）
    df = pd.read_csv(csv_path, low_memory=False)

    print(f"[LOAD] raw rows = {len(df)}")

    # 2️⃣ 保底欄位檢查（這段你留得非常好）
    required = {"open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    # 3️⃣ 清洗資料（關鍵）
    df = sanitize_kline_dataframe(df)
    print(f"[SANITIZE] clean rows = {len(df)}")

    if len(df) < 50:
        raise ValueError("Not enough clean rows to compute indicators")

    # 4️⃣ 計算指標（整段 dataframe → dataframe）
    from trading_core.analysis.indicators.indicator_bundle import (
        build_indicator_dataframe,
    )

    indicators_df = build_indicator_dataframe(df)

    # 5️⃣ 合併（index 對齊）
    out_df = pd.concat(
        [
            df.reset_index(drop=True),
            indicators_df.reset_index(drop=True),
        ],
        axis=1,
    )

    out_df.to_csv(out_path, index=False)

    print(f"✅ Indicator batch done: {out_path}")
    print(f"[DONE] total rows written = {len(out_df)}")


if __name__ == "__main__":
    TIMEFRAMES = {
        "15m": "trading_core/data/raw/binance_csv/BTC_USDT_15m.csv",
        "1h":  "trading_core/data/raw/binance_csv/BTC_USDT_1h.csv",
        "4h":  "trading_core/data/raw/binance_csv/BTC_USDT_4h.csv",
    }

    OUT_DIR = "trading_core/data/indicators"

    for interval, csv_path in TIMEFRAMES.items():
        out_path = f"{OUT_DIR}/BTC_USDT_{interval}_indicators.csv"

        print("\n" + "=" * 60)
        print(f"🚀 START indicator batch | interval={interval}")
        print("=" * 60)

        run_batch(
            csv_path=csv_path,
            out_path=out_path,
            interval=interval,
        )
