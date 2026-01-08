# shared_core/world/perception_attach_gate.py

class PerceptionAttachGate:
    """
    Gate for Perception Attach (World Runtime v1)

    職責：
    - 根據 WorldProfile.pipeline
    - 決定是否允許 perception adapters 掛載
    """

    def __init__(self, runtime, profile):
        self.runtime = runtime
        self.profile = profile

    def apply(self):
        enabled = bool(self.profile.pipeline.get("perception", False))

        if enabled:
            self._attach_perception()
        else:
            self._block_perception()

    # -------------------------------------------------
    # Internal
    # -------------------------------------------------
    def _attach_perception(self):
        # v1：什麼都不做，因為 Pandora 預設已 attach
        print("[PerceptionGate] 👁 Perception ENABLED by WorldProfile")

    def _block_perception(self):
        """
        阻擋 perception：
        - v1 做法：卸載 / 停用 perception adapters
        """
        print("[PerceptionGate] 🚫 Perception DISABLED by WorldProfile")

        # 依你目前系統，adapter key 有這些
        for key in ["market.kline", "text.input", "library.event"]:
            try:
                self.runtime.unregister_adapter(key)
                print(f"[PerceptionGate] ❌ Adapter removed: {key}")
            except Exception:
                # adapter 不存在就忽略
                pass
