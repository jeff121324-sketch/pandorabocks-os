import sys
from pathlib import Path
from datetime import datetime, timezone

# === 專案根目錄（aisop/） ===
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from shared_core.event_schema import PBEvent
from shared_core.governance.parliament.parliament_engine import ParliamentEngine
from shared_core.governance.handlers.governance_snapshot_handler import (
    GovernanceSnapshotHandler,
)
from shared_core.event.zero_copy_event_bus import ZeroCopyEventBus
def run():
    engine = ParliamentEngine(
        rules_path="shared_core/governance/parliament/rules.yaml"
    )
    bus = ZeroCopyEventBus()
    handler = GovernanceSnapshotHandler(engine, bus)

    # 模擬治理快照事件
    event = PBEvent(
        type="system.governance.snapshot.created",
        payload={
            "snapshot_id": "SNAP-TEST-001",
            "checksum": "dummy",
            "world_count": 2,
            "ts": "2025-01-01T00:00:00Z",
        },
        source="test",
    )

    decision = handler.handle(event)

    print("\n=== SNAPSHOT → PARLIAMENT ===")
    print(decision.outcome, decision.arbitration_required, decision.notes)


if __name__ == "__main__":
    run()
