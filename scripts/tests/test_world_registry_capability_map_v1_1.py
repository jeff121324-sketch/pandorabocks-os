
import sys
from pathlib import Path
from datetime import datetime, timezone

# === 專案根目錄（aisop/） ===
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pprint import pprint
from uuid import uuid4
from datetime import datetime, timezone
from shared_core.world.registry import WorldRegistry
from shared_core.world.world_context import WorldContext
from shared_core.world.capabilities import WorldCapabilities
from shared_core.governance.capability_snapshot import CapabilitySnapshot
from shared_core.event.zero_copy_event_bus import ZeroCopyEventBus
from shared_core.event_schema import PBEvent

def run():
    registry = WorldRegistry()
    event_bus = ZeroCopyEventBus()

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

    snapshot = registry.export_capability_snapshot()

    print(snapshot)
    print(snapshot.to_dict())
    print("checksum:", snapshot.checksum)
    # 🔁 再取一次 snapshot（同一個 registry 狀態）
    snapshot2 = registry.export_capability_snapshot()
    assert snapshot.worlds == snapshot2.worlds

    from shared_core.governance.capability_snapshot_writer import CapabilitySnapshotWriter
    from library.library_writer import LibraryWriter
    from library.library_event import LibraryEvent

    library_root = ROOT / "aisop" / "library"
    writer = LibraryWriter(library_root)

    snapshot = registry.export_capability_snapshot()

    event = LibraryEvent(
        event_id=str(uuid4()),
        event_type="world.capability.snapshot",
        source="governance.world_registry",
        payload=snapshot.to_dict(),
        ts=datetime.now(timezone.utc).isoformat(),
        weak_label=None,
        meta={
            "snapshot_checksum": snapshot.checksum,
            "schema": "capability_snapshot_v1.2",
        },
    )
    writer.write_event(event)
    print("✅ capability snapshot written to library")

    governance_event = PBEvent(
        type="system.governance.snapshot.created",
        payload={
            "snapshot_id": snapshot.snapshot_id,
            "checksum": snapshot.checksum,
            "world_count": len(snapshot.worlds),
            "ts": snapshot.timestamp,
        },
        source="governance.world_registry",
    )
    event_bus.publish(governance_event)
    print("📣 governance snapshot notification emitted")
if __name__ == "__main__":
    run()
