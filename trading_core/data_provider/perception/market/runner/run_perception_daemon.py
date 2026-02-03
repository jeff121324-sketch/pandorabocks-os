import sys
import os
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

    # =====================================================
    # ⭐ 1. Market Context（由 Launcher 傳入）
    # =====================================================
    symbol = os.getenv("AISOP_MARKET_SYMBOL", "BTC/USDT")

    intervals = os.getenv("AISOP_MARKET_INTERVALS", "15m").split(",")
    intervals = [i.strip() for i in intervals if i.strip()]

    if not intervals:
        raise RuntimeError("❌ No market intervals provided")

    # =====================================================
    # ⭐ 2. Core Components（共用）
    # =====================================================
    fetcher = BinanceRawFetcher()
    gateway = build_market_perception_gateway(mode="bootstrap")
    bus = ZeroCopyEventBus()
    csv_writer = MarketCSVWriter(root="trading_core/data/raw/binance_csv")

    # 每個 interval 各自計時
    last_run = {interval: 0 for interval in intervals}

    print(f"🟢 Market Perception Daemon started")
    print(f"📊 Symbol={symbol} Intervals={intervals}")

    # =====================================================
    # ⭐ 3. Risk Snapshot Runners（每 interval 一個）
    # =====================================================
    from trading_core.data_provider.perception.market.runner.run_risk_snapshot import (
        RiskSnapshotRunner,
    )

    risk_runners = []

    for interval in intervals:
        runner = RiskSnapshotRunner(
            bus=bus,
            symbol=symbol,
            interval=interval,
            window=120,
        )
        bus.subscribe("market.kline", runner.on_kline)
        risk_runners.append(runner)

    # =====================================================
    # ⭐ 4. Risk CSV Writers（每 interval 一個）
    # =====================================================
    from trading_core.analysis.risk.risk_csv_writer import RiskCSVWriter

    risk_csv_writers = {}

    for interval in intervals:
        writer = RiskCSVWriter(
            path=f"trading_core/data/raw/analysis/risk/BTC_USDT_{interval}_risk.csv"
        )
        bus.subscribe("risk.snapshot", writer.on_risk_snapshot)
        risk_csv_writers[interval] = writer

    # =====================================================
    # ⭐ 5. Indicator CSV Writers（每 interval 一個）
    # =====================================================
    from trading_core.analysis.indicators.indicator_csv_writer import (
        IndicatorCSVWriter,
    )

    indicator_csv_writers = {}

    for interval in intervals:
        writer = IndicatorCSVWriter(
            path=f"trading_core/data/raw/analysis/indicators/BTC_USDT_{interval}_indicators.csv"
        )
        bus.subscribe("indicator.snapshot", writer.on_indicator_snapshot)
        indicator_csv_writers[interval] = writer

    # =====================================================
    # ⭐ 6. Main Loop（多 interval 同步運作）
    # =====================================================
    print("🚀 Market system running")

    while True:
        now = time.time()

        for interval in intervals:
            seconds = INTERVAL_SECONDS.get(interval)
            if seconds is None:
                continue

            if now - last_run[interval] < seconds:
                continue

            print(f"[{datetime.now().isoformat()}] ▶ Fetch {interval}")

            # === Fetch market data ===
            raws = fetcher.fetch(symbol, interval)

            # === Write CSV ===
            csv_writer.write(raws, symbol=symbol, interval=interval)

            # === Publish events ===
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
