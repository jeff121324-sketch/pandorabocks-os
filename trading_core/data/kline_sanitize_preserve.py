import sys
from pathlib import Path
from datetime import datetime, timezone

# === 專案根目錄（aisop/） ===
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import argparse
from pathlib import Path
import shutil
import pandas as pd


# ======================================================
# 🔒 Final Canonical Column Order (你指定的)
# ======================================================
FINAL_COLUMNS = [
    "source",
    "market",
    "symbol",
    "interval",
    "kline_open_ts",
    "kline_close_ts",
    "fetch_ts",
    "human_open_time",
    "human_open_time_local",
    "open",
    "high",
    "low",
    "close",
    "volume",
]

NUMERIC_COLUMNS = [
    "kline_open_ts",
    "kline_close_ts",
    "fetch_ts",
    "open",
    "high",
    "low",
    "close",
    "volume",
]


def reorder_and_dedup(df: pd.DataFrame) -> pd.DataFrame:
    """
    - 欄位順序標準化
    - 數值可信化
    - 依 kline_close_ts 排序
    - 去除重複 K 線
    """

    df = df.copy()

    # === 1️⃣ 欄位存在檢查 ===
    missing = [c for c in FINAL_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # === 2️⃣ 數值型別轉換 ===
    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # === 3️⃣ 欄位重排 ===
    df = df[FINAL_COLUMNS]

    # === 4️⃣ 排序（以 close time 為準）===
    df = df.sort_values("kline_close_ts")

    # === 5️⃣ 去重（同一根 K 線只留一筆）===
    df = df.drop_duplicates(subset=["kline_close_ts"], keep="last")

    # === 6️⃣ 移除不完整 K 線（只針對 OHLC）===
    df = df.dropna(subset=["open", "high", "low", "close"])

    return df.reset_index(drop=True)


# ======================================================
# 🚀 In-place batch runner
# ======================================================
def main():
    parser = argparse.ArgumentParser(
        description="Reorder & deduplicate kline CSVs in-place"
    )
    parser.add_argument(
        "--dir",
        default=r"D:\aisop\trading_core\data\raw\binance_csv",
        help="Target directory (default: raw/binance_csv)",
    )
    parser.add_argument(
        "--pattern",
        default="*.csv",
        help="File pattern (default: *.csv)",
    )
    args = parser.parse_args()

    target_dir = Path(args.dir)
    if not target_dir.exists():
        raise FileNotFoundError(f"Directory not found: {target_dir}")

    files = sorted(target_dir.glob(args.pattern))
    if not files:
        print("⚠️ No CSV files found")
        return

    print(f"🧼 Reordering & deduplicating K-line CSVs")
    print(f"📂 {target_dir}")
    print(f"📄 files={len(files)}")

    for path in files:
        print(f"\n[PROCESS] {path.name}")

        # === 0️⃣ Backup ===
        bak = path.with_suffix(path.suffix + ".bak")
        if not bak.exists():
            shutil.copy2(path, bak)
            print("  ↳ backup created")

        # === 1️⃣ Load ===
        df = pd.read_csv(path, low_memory=False)

        # === 2️⃣ Clean ===
        df_clean = reorder_and_dedup(df)

        # === 3️⃣ Overwrite ===
        df_clean.to_csv(path, index=False)
        print(f"  ✅ rows written = {len(df_clean)}")

    print("\n🏁 All files normalized to final schema")


if __name__ == "__main__":
    main()

