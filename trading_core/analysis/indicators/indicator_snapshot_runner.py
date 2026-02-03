# trading_core/analysis/indicators/indicator_snapshot_runner.py

from datetime import datetime
from collections import deque

from shared_core.event_schema import PBEvent

from trading_core.analysis.indicators.indicator_bundle import (
    build_indicator_bundle,
)


class IndicatorSnapshotRunner:
    """
    Assemble indicators from market.kline
    Emit indicator.snapshot
    """

    def __init__(self, bus, symbol: str, interval: str, window: int = 120):
        self.bus = bus
        self.symbol = symbol
        self.interval = interval
        self.window = window
        self.buffer = deque(maxlen=window)

    def on_kline(self, event):
        payload = event.payload

        # === 基本過濾 ===
        if payload.get("symbol") != self.symbol:
            return
        if payload.get("interval") != self.interval:
            return

        # === 累積 K 線 ===
        self.buffer.append(payload)

        if len(self.buffer) < self.window:
            return  # 資料不足，不發 snapshot

        # === 組成 DataFrame ===
        df = pd.DataFrame(list(self.buffer))

        # === 計算指標（統一出口）===
        indicators = build_indicator_bundle(df)

        # === 發出 snapshot event ===
        snapshot_event = PBEvent(
            type="indicator.snapshot",
            payload={
                "timestamp": payload.get("close_time"),
                "symbol": self.symbol,
                "interval": self.interval,
                "indicators": indicators,
            },
            source="indicator_snapshot_runner",
        )

        self.bus.publish(snapshot_event)