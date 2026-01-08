import time
from trading_core.data_provider.perception.market.binance.binance_fetcher import (
    BinanceRawFetcher
)
from trading_core.data_provider.perception.market.storage.csv_market_writer import (
    MarketCSVWriter
)

def backfill(
    symbol: str,
    interval: str,
    from_ts: int,
    to_ts: int,
    csv_root: str,
):
    print(f"🔄 Backfill {symbol} {interval} from {from_ts} → {to_ts}")

    fetcher = BinanceRawFetcher()
    writer = MarketCSVWriter(root=csv_root)

    records = fetcher.fetch_history(
        symbol=symbol,
        interval=interval,
        since_ts=from_ts,
        until_ts=to_ts,
    )

    if records:
        writer.write(records)
        print(f"✅ Backfill done: {len(records)} records")
    else:
        print("ℹ️ No history needed")

    time.sleep(1)
