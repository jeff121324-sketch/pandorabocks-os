# tools/merge_legacy_market_data.py

import sys
import csv
import os
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from dateutil import parser as date_parser

# === 專案根目錄（aisop/） ===
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ========= 設定區 =========

LEGACY_FILES = {
    "15m": "legacy_data/market/BTC_USDT_15m.csv",
    "1h":  "legacy_data/market/BTC_USDT_1h.csv",
    "4h":  "legacy_data/market/BTC_USDT_4h.csv",
}

SYMBOL = "BTC/USDT"
MARKET = "crypto"
SOURCE = "legacy"

CSV_ROOT = "trading_core/data/raw/binance_csv"

INTERVAL_SECONDS = {
    "15m": 15 * 60,
    "1h":  60 * 60,
    "4h":  4 * 60 * 60,
}

LOCAL_TZ = ZoneInfo("Asia/Taipei")

# ========= 工具函式 =========

def parse_ts(value: str) -> int:
    """
    支援：
    - 秒 timestamp
    - 毫秒 timestamp
    - ISO datetime string（含時區）
    """
    value = value.strip()

    # 數字 timestamp
    try:
        ts = float(value)
        if ts > 1e12:  # 毫秒
            ts = ts / 1000
        return int(ts)
    except ValueError:
        pass

    # ISO datetime string
    dt = date_parser.parse(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def human_time(ts: int, tz):
    return datetime.fromtimestamp(ts, tz=tz).isoformat()


def read_csv_rows(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path, "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: str, rows: list[dict]):
    if not rows:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def normalize_legacy_row(row: dict, interval: str) -> dict:
    interval_sec = INTERVAL_SECONDS[interval]

    ts_key = (
        "timestamp"
        if "timestamp" in row
        else "open_time"
        if "open_time" in row
        else "time"
    )

    open_ts = parse_ts(row[ts_key])

    return {
        "source": SOURCE,
        "market": MARKET,
        "symbol": SYMBOL,
        "interval": interval,

        "kline_open_ts": open_ts,
        "kline_close_ts": open_ts + interval_sec,
        "fetch_ts": open_ts,

        "human_open_time": human_time(open_ts, timezone.utc),
        "human_open_time_local": human_time(open_ts, LOCAL_TZ),

        "open": float(row["open"]),
        "high": float(row["high"]),
        "low": float(row["low"]),
        "close": float(row["close"]),
        "volume": float(row["volume"]),
    }


def merge_row(existing: dict, legacy: dict) -> dict:
    """
    只補缺失欄位，不覆蓋既有世界事實
    """
    merged = dict(existing)
    for k, v in legacy.items():
        if k not in merged or merged[k] in ("", None):
            merged[k] = v
    return merged


# ========= 主合併流程 =========

def merge_interval(interval: str, legacy_path: str):
    print(f"🔧 Merging legacy data for {interval}")

    target_csv = f"{CSV_ROOT}/{SYMBOL.replace('/', '_')}_{interval}.csv"

    # 讀取現有世界事實
    existing_rows = read_csv_rows(target_csv)
    world = {}

    for row in existing_rows:
        ts = int(float(row["kline_open_ts"]))

        world[ts] = row

    # 讀取 legacy
    legacy_rows = read_csv_rows(legacy_path)

    added = 0
    patched = 0

    for row in legacy_rows:
        try:
            legacy = normalize_legacy_row(row, interval)
            ts = legacy["kline_open_ts"]

            if ts not in world:
                world[ts] = legacy
                added += 1
            else:
                merged = merge_row(world[ts], legacy)
                if merged != world[ts]:
                    world[ts] = merged
                    patched += 1
        except Exception as e:
            print(f"⚠️ Skip legacy row: {e}")

    # 依時間排序後重寫 CSV
    merged_rows = [world[k] for k in sorted(world.keys())]
    write_csv(target_csv, merged_rows)

    print(
        f"✅ {interval} merge done | "
        f"added={added}, patched={patched}, total={len(merged_rows)}"
    )


def main():
    print("🧬 Legacy Market Data MERGE started")

    for interval, legacy_path in LEGACY_FILES.items():
        if not os.path.exists(legacy_path):
            print(f"⚠️ Legacy file not found: {legacy_path}")
            continue

        merge_interval(interval, legacy_path)

    print("🎉 Legacy merge finished")
    print("👉 Next: run start_market_system.py to scan & backfill gaps")


if __name__ == "__main__":
    main()
