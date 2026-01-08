# shared_core/world/external_tick_attach_gate.py

from shared_core.world.capability_gate import WorldCapabilityGate
from shared_core.world.capability_types import WorldCapability


class ExternalTickAttachGate:
    """
    External Tick Attach Gate (World Runtime v1)

    職責：
    - 根據 WorldProfile.permission
    - 檢查世界是否允許 external tick
    - 決定是否 attach external tick source
    """

    def __init__(self, runtime, registry, profile):
        self.runtime = runtime
        self.registry = registry
        self.profile = profile
        self.gate = WorldCapabilityGate(registry)

    def apply(self):
        world_id = self.profile.world_id

        try:
            # 🔐 治理級檢查（唯一合法入口）
            self.gate.require(world_id, WorldCapability.EXTERNAL_TICK)
            self._attach_external_tick()

        except PermissionError:
            self._block_external_tick()

    # -------------------------------------------------
    # Internal
    # -------------------------------------------------
    def _attach_external_tick(self):
        """
        v1：不在這裡實際 attach 任何 source
        只宣告『這個世界允許活著』
        """
        print("[ExternalTickGate] 🫀 External tick ENABLED by WorldProfile")

    def _block_external_tick(self):
        """
        世界存在，但是『靜止的』
        """
        print("[ExternalTickGate] 🧊 External tick DISABLED by WorldProfile")
