
from shared_core.pb_lang.pb_event_validator import PBEventValidator
from shared_core.event_schema import PBEvent

class EventBus:
    """
    Pandora OS 的事件匯流排：
    - subscribe(event_type, callback)
    - emit(event_type, data)
    - publish(PBEvent)  ← PB-Lang 專用入口
    """

    def __init__(self, validator: PBEventValidator | None = None) -> None:
        self.listeners: dict[str, list] = {}
        self.validator = validator or PBEventValidator()

    # ------------------------------
    # 事件訂閱
    # ------------------------------
    def subscribe(self, event_type: str, callback):
        self.listeners.setdefault(event_type, []).append(callback)

    # ------------------------------
    # 事件廣播（已經是乾淨的 payload）
    # ------------------------------
    def emit(self, event_type: str, data=None):
        for cb in self.listeners.get(event_type, []):
            try:
                cb(data)
            except Exception as e:
                print(f"[EVENT ERROR] {event_type}: {e}")

    # ------------------------------
    # PB-Lang 事件入口
    # ------------------------------
    def publish(self, event: PBEvent):
        """
        PB-Lang v2 正式入口：
        1. 先丟給 PBEventValidator 檢查
        2. 檢查通過後，再把 payload 廣播出去
        """
        validated = self.validator.validate(event)
        self.emit(validated.type, validated.payload)