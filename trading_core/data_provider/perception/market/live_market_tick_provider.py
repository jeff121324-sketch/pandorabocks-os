# trading_core/data_provider/perception/market/live_market_tick_provider.py

class LiveMarketTickProvider:
    """
    Live market event bridge.
    - Receives in-progress market data
    - Emits to trading / execution layer
    - NO storage, NO history
    """

    def __init__(self):
        self._listeners = []

    def register(self, handler):
        """
        Register a callback:
        handler(event: dict)
        """
        self._listeners.append(handler)

    def emit_kline(
        self,
        source: str,
        market: str,
        symbol: str,
        interval: str,
        kline_open_ts: float,
        kline_close_ts: float,
        open: float,
        high: float,
        low: float,
        close: float,
        volume: float,
    ):
        event = {
            "type": "live.kline",
            "source": source,
            "market": market,
            "symbol": symbol,
            "interval": interval,
            "kline_open_ts": kline_open_ts,
            "kline_close_ts": kline_close_ts,
            "open": open,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }

        for handler in self._listeners:
            try:
                handler(event)
            except Exception:
                # live system must never crash
                pass
