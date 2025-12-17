# aisop_core/aisop_runtime.py

from datetime import datetime, timezone

from pandora_core.plugin_base import PluginBase
from shared_core.event_schema import PBEvent

class AISOPRuntime(PluginBase):
    """
    AISOP Runtime（Full Runtime 版）

    - 由 PandoraRuntime 的主迴圈定期呼叫 tick()
    - 可以自己決定何時對 EventBus 發事件（例如心跳、排程任務）
    - 之後要接飯店流程（checkout_flow、frontdesk_flow）都從這裡掛進去
    """

    def __init__(self, bus=None, config=None):
        super().__init__("AISOPRuntime")
        self.bus = bus
        self.config = config or {}

        # runtime 狀態
        self._started = False
        self._last_heartbeat_ts = None  # 上次心跳時間

        print("[AISOPRuntime] Initialized (full runtime mode)")

    # -------------------------------------------------
    # Bus 注入：由 PandoraRuntime.install_plugin() 呼叫
    # -------------------------------------------------
    def attach_bus(self, bus):
        """
        PluginBase.attach_bus() 的覆寫版本：
        讓 PandoraRuntime 在安裝 plugin 時可以把 bus 傳進來。
        """
        super().attach_bus(bus)
        self.bus = bus

    # -------------------------------------------------
    # Runtime lifecycle
    # -------------------------------------------------
    def start(self):
        """第一次被 tick 時啟動 Runtime。未來可以在這裡載入設定 / 模組。"""
        if self._started:
            return

        self._started = True
        print("[AISOPRuntime] 🚀 Runtime started")

        # TODO: 未來在這裡掛上各種 flow / 模組
        # self._init_flows()

    def tick(self):
        """
        由 PandoraRuntime 的主迴圈每次 tick 呼叫。
        Full Runtime 版的核心入口。
        """
        if not self._started:
            # 第一次 tick 自動 start
            self.start()

        # 目前先實作：每秒送出一次 AISOP 心跳事件
        now = datetime.now(timezone.utc)
        if (
            self._last_heartbeat_ts is None
            or (now - self._last_heartbeat_ts).total_seconds() >= 1.0
        ):
            self._last_heartbeat_ts = now
            self._send_heartbeat()

        # TODO: 未來在這裡呼叫各種 flow，例如：
        # self._run_checkout_flow()
        # self._run_frontdesk_flow()

    # -------------------------------------------------
    # Event handling（之後要訂閱特定事件可以用這裡）
    # -------------------------------------------------
    def on_event(self, event_type, data):
        """
        如果 AI Manager 或 EventBus 之後有 dispatch 特定事件給 AISOPRuntime，
        可以在這裡處理。
        """
        print(f"[AISOPRuntime] Event received: {event_type}, data={data}")

    # -------------------------------------------------
    # 內部工具：心跳事件
    # -------------------------------------------------
    def _send_heartbeat(self):
        """每秒送出一個簡單的 AISOP 心跳事件到 EventBus。"""
        print("[AISOPRuntime] 💓 heartbeat")

        if not self.bus:
            # 沒有 bus（例如獨立單元測試時），就只印 log
            return

        event = PBEvent(
            type="aisop.heartbeat",
            payload={"status": "alive"},
        )

        # EventBus 目前一定有 emit()，publish() 是相容別名
        try:
            self.bus.emit(event)
        except AttributeError:
            # 萬一之後你改成 publish() 也能相容
            self.bus.publish(event)