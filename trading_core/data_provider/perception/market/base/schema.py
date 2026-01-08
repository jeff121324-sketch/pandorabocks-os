"""
Raw Market Event Schema (Market-Agnostic)
"""

REQUIRED_FIELDS = [
    "source",      # binance / okx / nyse
    "market",      # crypto / equity
    "symbol",      # BTC/USDT
    "interval",    # 15m / 1h / 4h
    "market_ts",   # 世界時間
    "fetch_ts",    # 抓取時間
    "open",
    "high",
    "low",
    "close",
    "volume",
]
