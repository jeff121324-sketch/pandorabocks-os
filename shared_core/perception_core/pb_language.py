"""
pb_language.py
PB-Lang 編碼器（Perception Layer 3）
將任何資料轉換為 PB-Lang 統一格式。
"""

from datetime import datetime, timezone

class PBEncoder:
    def encode(self, event_type: str, payload: dict, source="unknown", meta=None):
        """
        event_type: 事件種類，例如 "kline", "guest_event", "order", "signal"
        payload: 真正的資料
        source: 來源，例如 "binance", "frontdesk", "system"
        meta: 附加資訊（可選）
        """

        if meta is None:
            meta = {}

        return {
            "type": event_type,
            "payload": payload,
            "source": source,
            "ts": datetime.now(timezone.utc).isoformat(),
            "meta": meta
        }
