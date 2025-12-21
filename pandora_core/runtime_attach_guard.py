from shared_core.world.capability_gate import WorldCapabilityGate
from shared_core.world.capability_types import WorldCapability


class RuntimeAttachGuard:
    """
    World-aware guard for runtime / plugin attachment.

    v1.2:
    - Plugin self-describes its identity & capability requirements
    - Fully backward-compatible with v1.0 / v1.1 plugins
    - Guard enforces rules, does not manage lifecycle
    """

    def __init__(self, capability_gate: WorldCapabilityGate):
        self._gate = capability_gate

    def ensure_can_attach(
        self,
        world_id: str,
        plugin_instance=None,
        plugin_name=None,   # ✅ 接受，但目前不用
        **kwargs,           # ✅ 吃掉未來擴充參數
    ):
        """
        Called before attaching a plugin/runtime.
        """

        # =========================
        # Plugin self-description
        # =========================
        plugin_name = getattr(
            plugin_instance,
            "plugin_name",
            plugin_instance.__class__.__name__,
        )

        required_caps = getattr(
            plugin_instance,
            "required_capabilities",
            [],
        )

        # =========================
        # Capability enforcement
        # =========================
        for cap in required_caps:
            self._gate.require(world_id, cap)

        print(
            f"[RuntimeAttachGuard] ✅ Plugin '{plugin_name}' "
            f"passed capability check (caps={list(required_caps)})"
        )

        return True
