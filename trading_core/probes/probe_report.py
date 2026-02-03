# trading_runtime/probes/probe_report.py

from dataclasses import dataclass, field
from typing import List, Optional
from trading_core.probes.data_epoch import DataEpoch

@dataclass
class ProbeAnomaly:
    code: str
    message: str
    open_time: Optional[int] = None
    extra: dict = field(default_factory=dict)


@dataclass
class ProbeReport:
    probe_name: str
    symbol: str
    interval: str
    status: str              # OK / WARN / ERROR
    last_open_time: Optional[int]
    anomalies: List[ProbeAnomaly] = field(default_factory=list)

    # 🆕 NEW: data semantic generation (safe, optional)
    data_epoch: Optional[DataEpoch] = None

    def is_ok(self) -> bool:
        return self.status == "OK"