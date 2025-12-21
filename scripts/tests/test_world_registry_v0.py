import sys
from pathlib import Path
from datetime import datetime, timezone

# === 專案根目錄（aisop/） ===
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from shared_core.world.registry import WorldRegistry
from shared_core.world.capabilities import WorldCapabilities
from shared_core.world.world_context import WorldContext

registry = WorldRegistry()

registry.register(
    WorldContext(
        world_id="pandora",
        world_type="os",
        owner="system",
        description="Pandora OS core world",
    )
)

registry.register(
    WorldContext(
        world_id="aisop-hotel",
        world_type="aisop",
        owner="org",
        description="AISOP Hotel Runtime",
    )
)
registry.register_capabilities(
    WorldCapabilities(
        world_id="pandora",
        supports_hotplug=True,
        supports_multi_runtime=True,
    )
)

print(registry.get_capabilities("pandora"))
worlds = registry.list_worlds()
print([w.world_id for w in worlds])
