import sys
from pathlib import Path
from datetime import datetime, timezone

# === 專案根目錄（aisop/） ===
ROOT = Path(__file__).resolve().parents[5]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# === Data Source ===
from trading_core.data_provider.perception.market.binance.binance_fetcher import (
    BinanceRawFetcher
)

# === Perception Ingress ===
from trading_core.perception.bootstrap import build_market_perception_gateway

# === EventBus（用你系統現有的） ===
from shared_core.event.zero_copy_event_bus import ZeroCopyEventBus   # ⚠️ 若實際路徑不同，換成你的

def main():
    # 1. 初始化 Downloader
    fetcher = BinanceRawFetcher()

    # 2. 初始化感知層入口（唯一）
    gateway = build_market_perception_gateway(mode="bootstrap")

    # 3. 取得 EventBus
    bus = ZeroCopyEventBus()

    # 4. 世界進來
    for interval in ["15m", "1h", "4h"]:
        raws = fetcher.fetch("BTC/USDT", interval)

        for raw in raws:
            gateway.process_and_publish(
                key="market.kline",
                raw=raw,
                bus=bus,
                soft=False,
            )

    print("✅ Binance BTC perception events published")


if __name__ == "__main__":
    main()