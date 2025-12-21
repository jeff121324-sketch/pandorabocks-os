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
from pandora_core.runtime_attach_guard import RuntimeAttachGuard
from shared_core.world.capability_types import WorldCapability


def run():
    registry = WorldRegistry()

    registry.register(WorldContext(
        world_id="pandora",
        world_type="pandora",
        owner="system",
    ))

    registry.register_capabilities(WorldCapabilities(
        world_id="pandora",
        supports_multi_runtime=False,  # ❌ 不允許
    ))

    gate = WorldCapabilityGate(registry)
    guard = RuntimeAttachGuard(gate)

    try:
        guard.before_attach("pandora", "TradingRuntime")
    except PermissionError as e:
        print("[OK BLOCKED]", e)


if __name__ == "__main__":
    run()
