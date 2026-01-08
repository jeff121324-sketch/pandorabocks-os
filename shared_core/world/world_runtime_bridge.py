# shared_core/world/world_runtime_bridge.py

from shared_core.world.world_context import WorldContext
from shared_core.world.capabilities import WorldCapabilities
from shared_core.world.registry import WorldRegistry


class WorldRuntimeBridge:
    """
    World Runtime Bridge v1

    職責：
    - 將 WorldProfile 轉為「被治理系統承認的世界」
    - 不執行世界
    - 不管理生命週期
    """

    def __init__(self, registry: WorldRegistry):
        self._registry = registry

    # -------------------------------------------------
    # Public API
    # -------------------------------------------------
    def register_world(self, profile) -> WorldContext:
        """
        將 WorldProfile 正式註冊為 WorldContext + Capabilities
        """

        # 1️⃣ 建立 WorldContext（世界靜態身分）
        ctx = WorldContext(
            world_id=profile.world_id,
            world_type=profile.domain,
            domain=profile.domain,          
            owner="system",
            description=profile.raw.get("description"),
            meta=profile.meta,
        )

        self._registry.register(ctx)

        # 2️⃣ 宣告 WorldCapabilities（只宣告，不等於啟用）
        caps = self._build_capabilities(profile)
        self._registry.register_capabilities(caps)

        return ctx

    # -------------------------------------------------
    # Internal
    # -------------------------------------------------
    def _build_capabilities(self, profile) -> WorldCapabilities:
        """
        將 WorldProfile.permission / mode 映射為 WorldCapabilities

        ⚠ 注意：
        - capability = 世界「理論上支援什麼」
        - 不是 runtime 是否已啟用
        """

        permission = profile.permission or {}
        mode = profile.mode or {}

        return WorldCapabilities(
            world_id=profile.world_id,
            supports_hotplug=bool(mode.get("hotplug", False)),
            supports_multi_runtime=bool(mode.get("multi_runtime", False)),
            supports_external_tick=bool(permission.get("allow_external_tick", False)),
        )
