
import sys
from pathlib import Path
from datetime import datetime, timezone

# === 專案根目錄（aisop/） ===
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pprint import pprint

from shared_core.world.registry import WorldRegistry
from shared_core.world.world_context import WorldContext
from shared_core.world.capabilities import WorldCapabilities


def run():
    registry = WorldRegistry()

    # 註冊 worlds
    registry.register(
        WorldContext(
            world_id="pandora",
            world_type="pandora",
            owner="system",
            description="Pandora OS Core Runtime",
        )
    )
    registry.register(
        WorldContext(
            world_id="aisop-hotel",
            world_type="aisop",
            owner="system",
            description="AISOP Hotel Runtime",
        )
    )

    # 註冊 capabilities（pandora 故意不宣告，測穩定輸出）
    registry.register_capabilities(
        WorldCapabilities(
            world_id="aisop-hotel",
            supports_hotplug=True,
            supports_multi_runtime=True,
            supports_external_tick=True,
        )
    )

    cap_map = registry.export_capability_map()

    print("\n[Capability Map]")
    pprint(cap_map)

    # 斷言：pandora 沒宣告也要穩定輸出
    assert cap_map["pandora"]["allowed_capabilities"] == [], "pandora should have empty capabilities"
    assert "EXTERNAL_TICK" in cap_map["aisop-hotel"]["allowed_capabilities"]
    assert "MULTI_RUNTIME" in cap_map["aisop-hotel"]["allowed_capabilities"]

    print("\n✅ World Registry v1.1 capability map test PASSED")


if __name__ == "__main__":
    run()
