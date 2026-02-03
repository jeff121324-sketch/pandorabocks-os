import json
import time
import threading
import websocket

from trading_core.data_provider.perception.market.live.base import LiveFeedBase


class BinanceWSFeed(LiveFeedBase):
    """
    Binance WebSocket live watcher.
    - in-progress kline only
    - no storage
    """

    def __init__(self, symbol: str, interval: str, provider):
        super().__init__(symbol, interval, provider)
        self._stop = False
        self.ws = None

    def start(self):
        t = threading.Thread(target=self._run, daemon=True)
        t.start()

    def stop(self):
        self._stop = True
        if self.ws:
            self.ws.close()

    def _run(self):
        sym = self.symbol.lower().replace("/", "")
        url = f"wss://stream.binance.com:9443/ws/{sym}@kline_{self.interval}"

        while not self._stop:
            try:
                self.ws = websocket.WebSocketApp(
                    url,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close,
                )
                self.ws.run_forever(ping_interval=20, ping_timeout=10)
            except Exception as e:
                print("[LIVE][binance] ws error, retry:", e)
                time.sleep(5)

    def _on_message(self, ws, message):
        try:
            msg = json.loads(message)
            k = msg.get("k")
            if not k:
                return

            # 已收盤 → 歷史系統處理，這裡不碰
            if k.get("x"):
                return

            # 即時「現在進行式」kline
            self.provider.emit_kline(
                source="binance_ws_live",
                market="crypto",
                symbol=self.symbol,
                interval=self.interval,
                kline_open_ts=k["t"] / 1000,
                kline_close_ts=k["T"] / 1000,
                open=float(k["o"]),
                high=float(k["h"]),
                low=float(k["l"]),
                close=float(k["c"]),
                volume=float(k["v"]),
            )
        except Exception:
            # live system: never crash
            pass

    def _on_error(self, ws, error):
        print("[LIVE][binance] error:", error)

    def _on_close(self, ws, *_):
        if not self._stop:
            print("[LIVE][binance] closed, reconnecting...")
