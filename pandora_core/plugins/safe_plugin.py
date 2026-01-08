import threading
import time
from pandora_core.plugin_base import PluginBase

class SafePlugin(PluginBase):
    plugin_name = "safe-plugin"

    def __init__(self, name):
        super().__init__(name)
        self._subs = []
        self._thread = None
        self.bus = None

    # --------------------------------------------------
    # 插件載入（熱插入）
    # --------------------------------------------------
    def on_load(self, bus):
        self.bus = bus
        self._active = True

        # 1️⃣ 訂閱事件（自己記錄）
        bus.subscribe("market.kline", self.on_kline)
        self._subs.append(("market.kline", self.on_kline))

        # 2️⃣ 啟動背景工作（可停止）
        self._thread = threading.Thread(
            target=self._loop,
            name="SafePluginThread",
            daemon=True,
        )
        self._thread.start()

        print("[SafePlugin] loaded")

    # --------------------------------------------------
    # 事件處理
    # --------------------------------------------------
    def on_kline(self, event):
        if not self._active:
            return
        # 👉 實際處理邏輯
        print("[SafePlugin] kline event")

    # --------------------------------------------------
    # 背景 loop（一定要看 _active）
    # --------------------------------------------------
    def _loop(self):
        while self._active:
            # 👉 背景工作
            time.sleep(1)

        print("[SafePlugin] background loop stopped")

    # --------------------------------------------------
    # 熱移除（Hot Unplug）
    # --------------------------------------------------
    def on_unload(self):
        # 1️⃣ 發出停止訊號
        self._active = False

        # 2️⃣ 解除事件訂閱
        for evt, handler in self._subs:
            try:
                self.bus.unsubscribe(evt, handler)
            except Exception as e:
                print(f"[SafePlugin] unsubscribe failed: {e}")

        self._subs.clear()

        print("[SafePlugin] unloaded safely")
