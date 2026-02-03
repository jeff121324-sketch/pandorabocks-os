from collections import defaultdict, deque
from typing import Deque, Dict, Optional

from .probe_report import ProbeReport, ProbeAnomaly
from trading_core.probes.data_epoch import DataEpoch

BASE_EPOCH_15M = DataEpoch(
    name="live_15m_v2",
    source="live",
    timeframe_policy="strict",
    trust_level="full",
)

DERIVED_EPOCH_HIGHER_TF = DataEpoch(
    name="legacy_higher_tf_v1",
    source="csv",
    timeframe_policy="derived",
    trust_level="degraded",
)
class KlineAlignmentProbe:
    """
    Phase 2 Probe (v1):
    - Verify cross-interval alignment (15m -> 1h)
    - Read-only, non-intrusive
    """

    PROBE_NAME = "kline_alignment_probe"

    BASE_INTERVAL = "15m"
    TARGET_INTERVAL = "1h"
    EXPECTED_BASE_COUNT = 4

    def __init__(self):
        # symbol -> deque of recent 15m klines
        self._base_buffer: Dict[str, Deque[dict]] = defaultdict(
            lambda: deque(maxlen=self.EXPECTED_BASE_COUNT)
        )

    def on_kline(self, event) -> Optional[ProbeReport]:
        payload = getattr(event, "payload", None)
        if not isinstance(payload, dict):
            return None

        symbol = payload.get("symbol")
        interval = payload.get("interval")
        open_time = payload.get("open_time")
        close_time = payload.get("close_time")

        if symbol is None or interval is None:
            return None

        # =====================================================
        # Base interval: collect 15m klines
        # =====================================================
        if interval == self.BASE_INTERVAL:
            self._base_buffer[symbol].append(payload)
            return None

        # =====================================================
        # Target interval: validate alignment when 1h arrives
        # =====================================================
        if interval != self.TARGET_INTERVAL:
            return None

        base_klines = self._base_buffer.get(symbol)
        if not base_klines or len(base_klines) < self.EXPECTED_BASE_COUNT:
            # Not enough base data to validate yet
            return None

        anomalies = []

        first_15m = base_klines[0]
        last_15m = base_klines[-1]

        # Rule 1: open_time alignment
        if open_time != first_15m.get("open_time"):
            anomalies.append(
                ProbeAnomaly(
                    code="OPEN_TIME_MISMATCH",
                    message="1h open_time does not match first 15m open_time",
                    open_time=open_time,
                    extra={
                        "expected": first_15m.get("open_time"),
                        "actual": open_time,
                    }
                )
            )

        # Rule 2: close_time alignment
        if close_time != last_15m.get("close_time"):
            anomalies.append(
                ProbeAnomaly(
                    code="CLOSE_TIME_MISMATCH",
                    message="1h close_time does not match last 15m close_time",
                    open_time=open_time,
                    extra={
                        "expected": last_15m.get("close_time"),
                        "actual": close_time,
                    }
                )
            )

        if anomalies:
            data_epoch = DERIVED_EPOCH_HIGHER_TF

            # ================================
            # Step 2.5 語意修正（關鍵）
            # ================================
            if data_epoch.trust_level == "degraded":
                status = "INFO"   # ← 關鍵不是 WARNING
            else:
                status = "WARNING"

            return ProbeReport(
                probe_name=self.PROBE_NAME,
                symbol=symbol,
                interval=self.TARGET_INTERVAL,
                status=status,
                last_open_time=open_time,
                anomalies=anomalies,
                data_epoch=data_epoch,
            )

        return ProbeReport(
            probe_name=self.PROBE_NAME,
            symbol=symbol,
            interval=self.TARGET_INTERVAL,
            status="OK",
            last_open_time=open_time,
        )