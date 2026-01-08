import sys
from pathlib import Path
from datetime import datetime

# === 專案根目錄 ===
ROOT = Path(__file__).resolve().parents[5]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import time
import subprocess
from datetime import datetime, timezone

# === Market Data ===
from trading_core.data_provider.perception.market.binance.binance_fetcher import (
    BinanceRawFetcher
)
from trading_core.data_provider.perception.market.storage.csv_market_writer import (
    MarketCSVWriter
)

# === Bootstrap Utils ===
from trading_core.data_provider.perception.market.runner.history_scanner import (
    scan_last_kline_ts
)
from trading_core.data_provider.perception.market.runner.backfill_history import (
    backfill
)


CSV_ROOT = "trading_core/data/raw/binance_csv"
SYMBOL = "BTC/USDT"

INTERVALS = {
    "15m": 15 * 60,
    "1h": 60 * 60,
    "4h": 4 * 60 * 60,
}

MAX_HISTORY_BARS = 20000

def now_ts():
    return int(time.time())

def main():
    print("🚀 Market System Bootstrap start")

    fetcher = BinanceRawFetcher()
    writer = MarketCSVWriter(root=CSV_ROOT)

    current_ts = now_ts()

    for interval, sec in INTERVALS.items():
        csv_path = f"{CSV_ROOT}/{SYMBOL.replace('/', '_')}_{interval}.csv"
        last_ts = scan_last_kline_ts(csv_path)

        # --------------------------------------------------
        # 🧊 Cold Start：CSV 不存在或為空
        # --------------------------------------------------
        if last_ts is None:
            print(f"🧊 Cold start detected for {interval}, backfill max history")

            records = fetcher.fetch_history_max(
                symbol=SYMBOL,
                interval=interval,
                max_bars=MAX_HISTORY_BARS,
            )

            writer.write(records)
            print(f"✅ Cold backfill done: {len(records)} records")
            continue

        # --------------------------------------------------
        # 🔵 Hot Start：只補缺口
        # --------------------------------------------------
        gap = current_ts - last_ts

        if gap > sec:
            print(
                f"🧭 {interval} gap detected: "
                f"{datetime.fromtimestamp(last_ts, tz=timezone.utc)} → now"
            )

            backfill(
                symbol=SYMBOL,
                interval=interval,
                from_ts=last_ts + sec,
                to_ts=current_ts,
                csv_root=CSV_ROOT,
            )
        else:
            print(f"✅ {interval} up to date")

    print("🟢 History bootstrap finished")
    print("▶ Starting realtime perception daemon")

    subprocess.Popen([
        "python",
        "trading_core/data_provider/perception/market/runner/run_perception_daemon.py"
    ])

    print("🟢 Market system running")

if __name__ == "__main__":
    main()
