# trading_core/data_provider/perception/market/live/registry.py

from trading_core.data_provider.perception.market.live.exchanges.binance_ws import (
    BinanceWSFeed,
)

LIVE_FEED_REGISTRY = {
    "binance": BinanceWSFeed,
    # "okx": OKXWSFeed,
    # "bybit": BybitWSFeed,
}
