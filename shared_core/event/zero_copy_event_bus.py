# shared_core/event/zero_copy_event_bus.py

class ZeroCopyEventBus:
    """
    Zero-Copy EventBus：
    - 不複製事件物件（不 deepcopy）
    - 不複製 payload（傳參考）
    - handler 直接吃 event object
    - 大幅減少 CPU 負載
    """

    def __init__(self):
        # event_type → [handlers]
        self._subscribers = {}

    # --------------------------------------
    # 訂閱事件
    # --------------------------------------
    def subscribe(self, event_type: str, handler):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    # --------------------------------------
    # 發布事件（不複製）
    # --------------------------------------
    def publish(self, event):
        handlers = self._subscribers.get(event.type, [])
        for h in handlers:
            h(event)  # 直接傳 event（zero copy）

    # --------------------------------------
    # 訂閱所有事件（萬用監聽）
    # --------------------------------------
    def subscribe_all(self, handler):
        if "*" not in self._subscribers:
            self._subscribers["*"] = []
        self._subscribers["*"].append(handler)

    def publish_all(self, event):
        for h in self._subscribers.get("*", []):
            h(event)
