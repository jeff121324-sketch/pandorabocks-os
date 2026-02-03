# trading_runtime/probes/kline_integrity_probe.py

from collections import defaultdict
from typing import Dict, Optional

from .probe_report import ProbeReport, ProbeAnomaly


class KlineIntegrityProbe:
    """
    Phase 1 Probe:
    - Verify monotonic open_time per (symbol, interval)
    - Read-only, no decision, no state mutation outside itself
    """

    PROBE_NAME = "kline_integrity_probe"

    def __init__(self):
        # (symbol, interval) -> last_open_time
        self._last_open_time: Dict[tuple, Optional[int]] = defaultdict(lambda: None)

    def on_kline(self, event) -> Optional[ProbeReport]:
        """
        Expected event attributes:
        - event.symbol
        - event.interval
        - event.open_time (ms)
        """

        payload = getattr(event, "payload", None)
        if not isinstance(payload, dict):
            return None

        symbol = payload.get("symbol")
        interval = payload.get("interval")
        open_time = payload.get("open_time")

        # Guard: incomplete event, ignore silently
        if symbol is None or interval is None or open_time is None:
            return None

        key = (symbol, interval)
        last_time = self._last_open_time[key]

        anomalies = []

        if last_time is not None:
            if open_time <= last_time:
                anomalies.append(
                    ProbeAnomaly(
                        code="NON_MONOTONIC_TIME",
                        message="open_time is not strictly increasing",
                        open_time=open_time,
                        extra={
                            "last_open_time": last_time
                        }
                    )
                )

        # update internal state (allowed: probe-local state)
        self._last_open_time[key] = open_time

        if anomalies:
            return ProbeReport(
                probe_name=self.PROBE_NAME,
                symbol=symbol,
                interval=interval,
                status="ERROR",
                last_open_time=open_time,
                anomalies=anomalies
            )

        return ProbeReport(
            probe_name=self.PROBE_NAME,
            symbol=symbol,
            interval=interval,
            status="OK",
            last_open_time=open_time,
            anomalies=[]
        )
