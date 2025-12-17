# shared_core/event_schema.py
from __future__ import annotations
import uuid
import re
from datetime import datetime, timezone
from typing import Optional 
from shared_core.foundation.data_unit import DataUnit


class PBEvent(DataUnit):
    """
    PB-Lang Event (通用事件語言)
    Pandora OS / Trading Core / AISOP 通用事件格式
    """

    TYPE_PATTERN = re.compile(r"^[a-zA-Z0-9_]+(\.[a-zA-Z0-9_]+)+$")

    def __init__(
        self,
        type: str,
        payload: dict = None,
        source: str = "unknown",
        priority: int = 1,
        tags: list[str] = None,
        event_id: str = None,
        timestamp: str = None,
        ts: float | None = None,
    ):

        # --- 事件名稱格式驗證 ---
        self._validate_type(type)

        self.event_id = event_id or str(uuid.uuid4())
        self.type = type
        self.payload = payload or {}
        self.source = source

        # ⭐ PBEvent 與 DataUnit 統一 ID
        unit_id = self.event_id

        # ⭐ PBEvent 的 meta 會與 DataUnit meta 合併
        event_meta = {
            "lang": "PB-Lang v2",
            "priority": priority,
            "tags": tags or [],
            "source": source,
        }

        # ⭐ 呼叫父類別 DataUnit.__init__()
        super().__init__(
            unit_type="event",
            content=self.payload,
            meta=event_meta,
        )

        # DataUnit 會自己產生 unit_id → 我們覆蓋掉它
        self.unit_id = unit_id

        # --- 時間處理 ---
        if ts is not None:
            # 使用 UNIX timestamp
            self.ts = float(ts)
            self.timestamp = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()

        else:
            # 使用 ISO 時間字串
            self.timestamp = timestamp or self._now()
            try:
                self.ts = datetime.fromisoformat(self.timestamp).timestamp()
            except:
                self.ts = time.time()

        # 優先級 / 標籤
        self.priority = priority
        self.tags = tags or []
    # ------------------------------
    # Utility：現在時間 ISO 字串
    # ------------------------------
    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


    @classmethod
    def _validate_type(cls, t: str):
        """確保事件名稱格式正確，避免 wildcard routing 錯亂"""
        if not cls.TYPE_PATTERN.match(t):
            raise ValueError(f"Invalid PBEvent type format: {t}")

    def to_dict(self):
        base = super().to_dict()  # 來自 DataUnit，提供統一序列化
        base.update({
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "type": self.type,
            "source": self.source,
            "payload": self.payload,
            "meta": self.meta,
        })
        return base

    def __repr__(self):
        return f"<PBEvent {self.type} id={self.event_id}>"

