# shared_core/foundation/data_unit.py
from __future__ import annotations
import uuid
from datetime import datetime, timezone


class DataUnit:
    """
    🌐 Pandora OS Foundation Layer
    DataUnit = 整個文明的最小資訊單位。

    Event、State、Action、LogEntry 全部繼承它。
    """

    def __init__(self, unit_type: str, content: dict | None = None, meta: dict | None = None):
        self.unit_id = str(uuid.uuid4())
        self.unit_type = unit_type               # e.g. "event", "state", "action"
        self.timestamp = self._now()             # 全文明統一時間
        self.content = content or {}             # 真正的資料
        self.meta = meta or {}                   # 補充資訊（語言版本、priority...）

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()

    def to_dict(self):
        return {
            "unit_id": self.unit_id,
            "unit_type": self.unit_type,
            "timestamp": self.timestamp,
            "content": self.content,
            "meta": self.meta,
        }

    def __repr__(self):
        return f"<DataUnit type={self.unit_type} id={self.unit_id}>"

