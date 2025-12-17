
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, Optional
import json
from pathlib import Path
import uuid


@dataclass(frozen=True)
class LibraryEvent:
    """
    Library v1 — 文明級不可變記憶事件
    """

    # === 核心識別 ===
    event_id: str
    event_type: str        # 原 PBEvent.type
    source: str            # replay / live / simulation / audit

    # === 內容 ===
    payload: Dict[str, Any]

    # === 時間 ===
    ts: str                # ISO-8601 UTC

    # === 弱標籤（可選）===
    weak_label: Optional[Dict[str, Any]] = None

    # === 預留 meta（非 PBEvent.meta）===
    meta: Optional[Dict[str, Any]] = None

    # ---------- Factory ----------

    @staticmethod
    def from_pbevent(pbevent, *, weak_label=None, meta=None) -> "LibraryEvent":
        """
        將 PBEvent 昇華為 LibraryEvent（記憶單元）
        """
        return LibraryEvent(
            event_id=pbevent.event_id,
            event_type=pbevent.type,
            source=getattr(pbevent, "source", "unknown"),
            payload=pbevent.payload,
            ts=pbevent.timestamp
               or datetime.now(timezone.utc).isoformat(),
            weak_label=weak_label,
            meta=meta,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)
