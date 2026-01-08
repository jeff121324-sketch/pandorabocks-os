# data_provider/raw_fetcher.py
"""
LEGACY / PROTOTYPE FETCHER

This file was used during early perception pipeline validation.
It is kept for reference only.

⚠️ Do NOT extend this file.
⚠️ New market fetchers must be implemented under:
    data_provider/perception/market/
"""
import time

class RawMarketFetcher:
    """
    Raw Market Fetcher
    - 回傳原始市場事實（dict）
    - 不做任何 dataframe / 指標處理
    """

    def fetch(self, symbol: str, interval: str, limit=2):
        now = time.time()

        # v1 mock（先不接交易所）
        return [
            {
                "source": "mock",
                "symbol": symbol,
                "interval": interval,
                "market_ts": now - 60,
                "fetch_ts": now,
                "open": 1.0,
                "high": 2.0,
                "low": 0.5,
                "close": 1.8,
                "volume": 100,
            },
            {
                "source": "mock",
                "symbol": symbol,
                "interval": interval,
                "market_ts": now,
                "fetch_ts": now,
                "open": 1.8,
                "high": 2.1,
                "low": 1.7,
                "close": 2.0,
                "volume": 120,
            },
        ]
