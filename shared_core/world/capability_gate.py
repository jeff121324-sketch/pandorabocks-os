# shared_core/world/capability_gate.py

from shared_core.world.registry import WorldRegistry
from shared_core.world.capabilities import WorldCapabilities
from shared_core.world.capability_types import WorldCapability

class WorldCapabilityGate:
    def __init__(self, registry: WorldRegistry):
        self._registry = registry

    def require(self, world_id: str, capability: WorldCapability):
        caps = self._registry.get_capabilities(world_id)
        if caps is None:
            # 讓錯誤訊息跟你現在系統一致（你 log 裡就是這句）
            raise PermissionError(f"World '{world_id}' has no capabilities declared")

        allowed = getattr(caps, capability.value, False)
        if not allowed:
            raise PermissionError(
                f"World '{world_id}' does not support capability: {capability.name}"
            )

        return True