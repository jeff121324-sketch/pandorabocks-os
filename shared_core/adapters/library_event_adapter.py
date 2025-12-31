# shared_core/adapters/library_event_adapter.py

from shared_core.event_schema import PBEvent

from datetime import datetime, timezone

class LibraryEventAdapter:
    """
    Adapter for Library replay / learning
    - 不下單
    - 不發 EventBus
    - 只轉交給上層（LearningBrain / Analyzer）
    """

    KEY = "library.event"

    def __init__(self, validator=None):
        self.validator = validator

    def make_event(self, raw: dict) -> PBEvent:
        """
        raw: dict from Library jsonl
        """

        etype = raw.get("event_type") or raw.get("type")
        if not etype:
            raise ValueError("Library record missing event_type")

        payload = raw.get("payload") or {}
        source = raw.get("source", "library")

        event_id = raw.get("event_id")
        timestamp = raw.get("timestamp")  # ISO string
        meta = raw.get("meta", {})

        # tags / priority（若 Library 有就吃，沒有就用預設）
        tags = meta.get("tags") if isinstance(meta, dict) else None
        priority = meta.get("priority", 1) if isinstance(meta, dict) else 1

        # 若沒有 timestamp，補一個
        if not timestamp:
            timestamp = datetime.now(timezone.utc).isoformat()

        event = PBEvent(
            type=etype,            # ✅ 關鍵
            payload=payload,       # ✅ 關鍵
            source=source,
            priority=priority,
            tags=tags,
            event_id=event_id,
            timestamp=timestamp,
        )

        if self.validator and not event.type.startswith("library."):
            self.validator.validate(event)

        return event