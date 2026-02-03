# perception/market/runner/run_risk_snapshot.py

from collections import deque
from typing import Dict
from datetime import datetime

from trading_core.analysis.indicators.indicator_bundle import build_indicator_bundle
from trading_core.analysis.indicator_snapshot import IndicatorSnapshot
from trading_core.risk.market_risk_snapshot import build_market_risk_snapshot

from shared_core.event_schema import PBEvent


class RiskSnapshotRunner:
    """
    將 market.kline → risk.snapshot
    不做判斷、不做 gating，只做轉換
    """

    def __init__(self, bus, symbol: str, interval: str, window: int = 100):
        self.bus = bus
        self.symbol = symbol
        self.interval = interval
        self.window = window
        self.buffer = deque(maxlen=window)

    def on_kline(self, event):
        k = event.payload

        # 只吃自己負責的 symbol / interval
        if k.get("symbol") != self.symbol:
            return
        if k.get("interval") != self.interval:
            return

        self.buffer.append(k)

        # 最小保護：資料不足就不發
        if len(self.buffer) < 20:
            return

        # === 轉成 DataFrame ===
        import pandas as pd
        df = pd.DataFrame(list(self.buffer))

        # === Indicator Snapshot ===
        indicators = build_indicator_bundle(df)
        indicator_snapshot = IndicatorSnapshot(values=indicators)

        # === Risk Snapshot ===
        risk_snapshot = build_market_risk_snapshot(indicator_snapshot.values)

        # === Event 化 ===
        event = PBEvent(
            type="risk.snapshot",
            payload={
                "symbol": self.symbol,
                "interval": self.interval,
                "timestamp": k.get("close_time"),
                "risk": risk_snapshot.__dict__,
            },
            source="risk_snapshot_runner",
            priority=1,
            tags=["risk", "snapshot", "analysis"],
        )

        self.bus.publish(event)
