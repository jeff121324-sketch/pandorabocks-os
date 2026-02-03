# trading_core/data_provider/perception/market/live/runner.py

import argparse
import time

from trading_core.data_provider.perception.market.live.registry import (
    LIVE_FEED_REGISTRY,
)
from trading_core.data_provider.perception.market.live_market_tick_provider import (
    LiveMarketTickProvider,
)


def main():
    parser = argparse.ArgumentParser("Live Market Watcher")
    parser.add_argument("--exchange", required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--interval", required=True)

    args = parser.parse_args()

    feed_cls = LIVE_FEED_REGISTRY.get(args.exchange)
    if not feed_cls:
        raise ValueError(f"Unsupported exchange: {args.exchange}")

    provider = LiveMarketTickProvider()\
    
    def debug_print(event):
        print("[LIVE EVENT]", event)


    provider = LiveMarketTickProvider()
    provider.register(debug_print)
    feed = feed_cls(
        symbol=args.symbol,
        interval=args.interval,
        provider=provider,
    )

    print(
        f"[LIVE] start exchange={args.exchange} "
        f"symbol={args.symbol} interval={args.interval}"
    )

    feed.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[LIVE] stopping...")
        feed.stop()

def debug_print(event):
    print("[LIVE EVENT]", event)


provider = LiveMarketTickProvider()
provider.register(debug_print)

if __name__ == "__main__":
    main()
