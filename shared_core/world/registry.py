from typing import Dict, List, Optional, Any

from .world_context import WorldContext
from .capabilities import WorldCapabilities
from .capability_types import WorldCapability
from shared_core.governance.capability_snapshot import CapabilitySnapshot


class WorldRegistry:
    """
    世界註冊表（唯一事實來源）
    v0：只負責登記與查詢
    """

    def __init__(self):
        self._worlds: Dict[str, WorldContext] = {}
        self._capabilities: Dict[str, WorldCapabilities] = {}

    def register(self, world: WorldContext) -> None:
        if world.world_id in self._worlds:
            raise ValueError(f"World already exists: {world.world_id}")
        self._worlds[world.world_id] = world

    def get(self, world_id: str) -> WorldContext:
        if world_id not in self._worlds:
            raise KeyError(f"World not found: {world_id}")
        return self._worlds[world_id]

    def list_worlds(self) -> List[WorldContext]:
        return list(self._worlds.values())

    def register_capabilities(self, caps: WorldCapabilities) -> None:
        if caps.world_id not in self._worlds:
            raise KeyError(f"World not registered: {caps.world_id}")
        self._capabilities[caps.world_id] = caps

    def get_capabilities(self, world_id: str) -> WorldCapabilities:
        return self._capabilities.get(world_id)
    
    # =========================================================
    # v1.1 — Capability Map
    # =========================================================
    def export_capability_map(self) -> Dict[str, Dict[str, Any]]:
        """
        Export world capability map for auditing / reporting / routing.

        Returns:
            {
              "<world_id>": {
                "world_type": ...,
                "owner": ...,
                "description": ...,
                "capability_flags": {...},
                "allowed_capabilities": ["MULTI_RUNTIME", ...]
              },
              ...
            }
        """
        out: Dict[str, Dict[str, Any]] = {}

        for world_id, world in self._worlds.items():
            caps = self._capabilities.get(world_id)

            # flags（即使沒宣告，也要穩定輸出）
            flags = {
                "supports_hotplug": False,
                "supports_multi_runtime": False,
                "supports_external_tick": False,
            }
            if caps is not None:
                flags = {
                    "supports_hotplug": bool(caps.supports_hotplug),
                    "supports_multi_runtime": bool(caps.supports_multi_runtime),
                    "supports_external_tick": bool(caps.supports_external_tick),
                }

            # allowed_capabilities（由 flags 推導）
            allowed = []
            for cap in WorldCapability:
                flag_name = cap.value  # e.g. "supports_external_tick"
                if flags.get(flag_name, False):
                    allowed.append(cap.name)  # e.g. "EXTERNAL_TICK"

            out[world_id] = {
                "world_type": world.world_type,
                "owner": world.owner,
                "description": world.description,
                "capability_flags": flags,
                "allowed_capabilities": allowed,
            }

        return out
    def export_capability_snapshot(self) -> CapabilitySnapshot:
        """
        Governance-level snapshot of current world capability state.

        IMPORTANT:
        - Pure transformation
        - No side effects
        - No library write
        - No event emission
        """

        capability_map = self.export_capability_map()

        snapshot = CapabilitySnapshot(
            source="WorldRegistry.export_capability_snapshot",
            worlds=capability_map,
        )

        return snapshot
