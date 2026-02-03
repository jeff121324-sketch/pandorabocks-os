# trading_core/data_provider/perception/market/runner/live_market_tick_provider.py

from typing import Callable, Optional
from datetime import datetime, timezone
import time
from shared_core.event_schema import PBEvent

class LiveMarketTickProvider:
    """
    LiveMarketTickProvider v1

    職責：
    - 接收即時市場感知（Kline）
    - 轉為 PBEvent
    - 推送給 Pandora External Tick callback

    不負責：
    - 決策
    - 儲存
    - 時間補齊
    """

    def __init__(self, world_id: str):
        self.world_id = world_id
        self._callback: Optional[Callable[[PBEvent], None]] = None
        self._running = False
        # 🆕 Dedup cache
        self._seen = set()
        self._last_open_ts = {}   
        self._startup_emitted = False
    # =========================================================
    # Pandora 接口
    # =========================================================

    def start(self, callback: Callable[[PBEvent], None]):
        """
        Pandora ExternalTickExecutor 會呼叫這個方法
        """
        self._callback = callback
        self._running = True

        print(
            f"[LiveMarketTickProvider] 🟢 started "
            f"(world={self.world_id})"
        )

        if not getattr(self, "_startup_emitted", False):
            self._startup_emitted = True

            now_ms = int(time.time() * 1000)

            self.emit_kline(
                symbol="BTC/USDT",
                interval="1m",
                open_time_ms=now_ms,
                close_time_ms=now_ms,
                open_price=0,
                high_price=0,
                low_price=0,
                close_price=0,
                volume=0,
                source="startup_probe",
            )

    def stop(self):
        self._running = False
        print(
            f"[LiveMarketTickProvider] 🔴 stopped "
            f"(world={self.world_id})"
        )

    def _interval_to_ms(self, interval: str) -> int:
        if interval.endswith("m"):
            return int(interval[:-1]) * 60_000
        if interval.endswith("h"):
            return int(interval[:-1]) * 60 * 60_000
        raise ValueError(f"Unknown interval: {interval}")
    # =========================================================
    # Market Daemon 呼叫接口
    # =========================================================

    def emit_kline(
        self,
        *,
        symbol: str,
        interval: str,
        open_time_ms: int,
        close_time_ms: int,
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float,
        volume: float,
        source: str = "live",
    ):
        """
        由市場感知 daemon 呼叫
        """

        if not self._running or self._callback is None:
            return

        # ======================================================
        # 🛑 Dedup Guard（交易世界第一層安全）
        # ======================================================
        dedup_key = (
            symbol,
            interval,
            open_time_ms,
        )

        if dedup_key in self._seen:
            return  # 同一根 K 線，直接丟棄

        self._seen.add(dedup_key)
        # ======================================================

        # ======================================================
        # 🟡 Gap Detection（只警告，不補）
        # ======================================================
        key = (symbol, interval)
        last_ts = self._last_open_ts.get(key)

        now_ms = int(time.time() * 1000)
        interval_ms = self._interval_to_ms(interval)

        if last_ts is not None:
            if now_ms - last_ts > 2 * interval_ms:
                warn_event = PBEvent(
                    type="world.health.warning",
                    payload={
                        "world_id": self.world_id,
                        "mode": "live",
                        "reason": "kline_gap_detected",
                        "symbol": symbol,
                        "interval": interval,
                        "last_open_time": last_ts,
                        "now": now_ms,
                    },
                    source="live_market_tick_provider",
                    tags=["health", "warning", "kline_gap"],
                )
                self._callback(warn_event)

        # 更新最後一根 K 線時間
        self._last_open_ts[key] = open_time_ms

        # ======================================================
        # 📈 正常送出 market.kline
        # ======================================================
        event = PBEvent(
            type="market.kline",
            payload={
                "symbol": symbol,
                "interval": interval,
                "open_time": open_time_ms,
                "close_time": close_time_ms,
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": volume,
                "source": source,

                "world_id": self.world_id,
                "ingest_ts": self._now(),
                "mode": "live",
            },
            source=source,                      # "startup_probe" / "daemon"
            priority=1,
            tags=["market", "kline", source],   # 可選但推薦
        )

        self._callback(event)
    

    # =========================================================
    # Utils
    # =========================================================

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()
