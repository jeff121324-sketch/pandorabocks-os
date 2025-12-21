import sys
from pathlib import Path
from datetime import datetime, timezone

# === 專案根目錄（aisop/） ===
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
    
from shared_core.world.registry import WorldRegistry
from shared_core.world.world_context import WorldContext
from shared_core.world.capabilities import WorldCapabilities
from shared_core.world.capability_gate import WorldCapabilityGate
from shared_core.world.capability_types import WorldCapability

def run():
    registry = WorldRegistry()

    registry.register(WorldContext(
        world_id="pandora",
        world_type="pandora",
        owner="system",
        description="Pandora OS core world",
    ))

    registry.register_capabilities(WorldCapabilities(
        world_id="pandora",
        supports_hotplug=True,
        supports_multi_runtime=True,
        supports_external_tick=False,
    ))

    gate = WorldCapabilityGate(registry)

    # ✅ allowed
    gate.require("pandora", WorldCapability.HOTPLUG)

    # ❌ blocked
    try:
        gate.require("pandora", WorldCapability.EXTERNAL_TICK)
    except PermissionError as e:
        print("[OK BLOCKED]", e)

if __name__ == "__main__":
    run()

