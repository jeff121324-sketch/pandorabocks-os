# trading_core/analysis/indicator_snapshot.py

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class IndicatorSnapshot:
    """
    Analysis-layer indicator snapshot
    - 不做判斷
    - 不限制指標數量
    - 永遠可擴充
    """
    values: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default=None):
        return self.values.get(key, default)

    def as_dict(self) -> Dict[str, Any]:
        return dict(self.values)

    # === 可選：語意化存取（不強制） ===
    @property
    def rsi(self):
        return self.values.get("rsi")

    @property
    def atr(self):
        return self.values.get("atr")

    @property
    def composite_ready(self) -> bool:
        """
        是否具備進入 risk layer 的最低條件
        （不等於允許交易）
        """
        required = ["rsi", "atr", "adx", "vol_ratio"]
        return all(k in self.values for k in required)
