import sys
import time
from pathlib import Path
from datetime import datetime

# === 專案根目錄 ===
ROOT = Path(__file__).resolve().parents[5]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# === Data Source ===
from trading_core.data_provider.perception.market.binance.binance_fetcher import (
    BinanceRawFetcher
)

# === Perception Ingress ===
from trading_core.perception.bootstrap import build_market_perception_gateway

# === EventBus ===
from shared_core.event.zero_copy_event_bus import ZeroCopyEventBus
from trading_core.data_provider.perception.market.storage.csv_market_writer import MarketCSVWriter

from trading_core.data_provider.perception.market.runner.live_market_tick_provider import (
    LiveMarketTickProvider
)
INTERVAL_SECONDS = {
    "15m": 15 * 60,
    "1h": 60 * 60,
    "4h": 4 * 60 * 60,
}
def normalize_kline(raw: dict) -> dict:
    """
    Normalize raw kline into canonical schema for LiveMarketTickProvider
    """

    # ✅ AISOP Kline Raw v1（你現在用的）
    if "kline_open_ts" in raw and "kline_close_ts" in raw:
        return {
            "open_time": raw["kline_open_ts"],
            "close_time": raw["kline_close_ts"],
            "open": float(raw["open"]),
            "high": float(raw["high"]),
            "low": float(raw["low"]),
            "close": float(raw["close"]),
            "volume": float(raw["volume"]),
        }

    # 舊內部格式（保留，避免未來踩雷）
    if "open_time" in raw:
        return {
            "open_time": raw["open_time"],
            "close_time": raw["close_time"],
            "open": raw["open"],
            "high": raw["high"],
            "low": raw["low"],
            "close": raw["close"],
            "volume": raw["volume"],
        }

    # Binance 原始格式（保留）
    if "openTime" in raw:
        return {
            "open_time": raw["openTime"],
            "close_time": raw["closeTime"],
            "open": float(raw["open"]),
            "high": float(raw["high"]),
            "low": float(raw["low"]),
            "close": float(raw["close"]),
            "volume": float(raw["volume"]),
        }

    raise ValueError(
        f"Unknown kline format: {list(raw.keys())}"
    )



def main():
    fetcher = BinanceRawFetcher()
    gateway = build_market_perception_gateway(mode="bootstrap")
    bus = ZeroCopyEventBus()
    csv_writer = MarketCSVWriter(root="trading_core/data/raw/binance_csv")


    last_run = {k: 0 for k in INTERVAL_SECONDS}

    print("🟢 Market Perception Daemon started")

    while True:
        now = time.time()

        for interval, seconds in INTERVAL_SECONDS.items():
            if now - last_run[interval] < seconds:
                continue

            print(f"[{datetime.now().isoformat()}] ▶ Fetch {interval}")

            raws = fetcher.fetch("BTC/USDT", interval)
            csv_writer.write(raws)

            for raw in raws:
                gateway.process_and_publish(
                    key="market.kline",
                    raw=raw,
                    bus=bus,
                    soft=False,
                )


            last_run[interval] = now
            print(f"[{datetime.now().isoformat()}] ✅ Done {interval}")

        time.sleep(1)



if __name__ == "__main__":
    main()
